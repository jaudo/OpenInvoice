"""Reports service for sales analytics."""

import csv
from io import StringIO
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional

from ..database.connection import Database


@dataclass
class DailySales:
    """Daily sales summary."""
    date: str
    total_sales: float
    invoice_count: int
    average_sale: float
    by_payment_method: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TopProduct:
    """Top selling product."""
    product_id: str
    product_name: str
    quantity_sold: int
    revenue: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PeriodReport:
    """Sales report for a period."""
    start_date: str
    end_date: str
    total_sales: float
    invoice_count: int
    average_sale: float
    daily_breakdown: list[DailySales] = field(default_factory=list)
    top_products: list[TopProduct] = field(default_factory=list)
    by_payment_method: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        data['daily_breakdown'] = [d.to_dict() if hasattr(d, 'to_dict') else d for d in self.daily_breakdown]
        data['top_products'] = [p.to_dict() if hasattr(p, 'to_dict') else p for p in self.top_products]
        return data


class ReportsService:
    """Service for generating sales reports."""

    def __init__(self, db: Database = None):
        """Initialize reports service."""
        self.db = db or Database()

    def daily_sales(self, date: str) -> DailySales:
        """
        Get sales summary for a specific date.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            DailySales summary
        """
        # Total sales and count
        row = self.db.fetchone(
            """
            SELECT
                COALESCE(SUM(total), 0) as total_sales,
                COUNT(*) as invoice_count
            FROM invoices
            WHERE DATE(created_at) = DATE(?)
            AND status != 'returned'
            """,
            (date,)
        )

        total_sales = row['total_sales'] if row else 0
        invoice_count = row['invoice_count'] if row else 0
        average_sale = total_sales / invoice_count if invoice_count > 0 else 0

        # Breakdown by payment method
        payment_rows = self.db.fetchall(
            """
            SELECT
                payment_method,
                COALESCE(SUM(total), 0) as total,
                COUNT(*) as count
            FROM invoices
            WHERE DATE(created_at) = DATE(?)
            AND status != 'returned'
            GROUP BY payment_method
            """,
            (date,)
        )

        by_payment = {
            row['payment_method']: {
                'total': row['total'],
                'count': row['count']
            }
            for row in payment_rows
        }

        return DailySales(
            date=date,
            total_sales=total_sales,
            invoice_count=invoice_count,
            average_sale=round(average_sale, 2),
            by_payment_method=by_payment
        )

    def period_sales(self, start_date: str, end_date: str) -> PeriodReport:
        """
        Get sales summary for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            PeriodReport with daily breakdown
        """
        # Total for period
        row = self.db.fetchone(
            """
            SELECT
                COALESCE(SUM(total), 0) as total_sales,
                COUNT(*) as invoice_count
            FROM invoices
            WHERE DATE(created_at) BETWEEN DATE(?) AND DATE(?)
            AND status != 'returned'
            """,
            (start_date, end_date)
        )

        total_sales = row['total_sales'] if row else 0
        invoice_count = row['invoice_count'] if row else 0
        average_sale = total_sales / invoice_count if invoice_count > 0 else 0

        # Daily breakdown
        daily_rows = self.db.fetchall(
            """
            SELECT
                DATE(created_at) as date,
                COALESCE(SUM(total), 0) as total_sales,
                COUNT(*) as invoice_count
            FROM invoices
            WHERE DATE(created_at) BETWEEN DATE(?) AND DATE(?)
            AND status != 'returned'
            GROUP BY DATE(created_at)
            ORDER BY date
            """,
            (start_date, end_date)
        )

        daily_breakdown = [
            DailySales(
                date=row['date'],
                total_sales=row['total_sales'],
                invoice_count=row['invoice_count'],
                average_sale=round(row['total_sales'] / row['invoice_count'], 2) if row['invoice_count'] > 0 else 0
            )
            for row in daily_rows
        ]

        # Payment method breakdown
        payment_rows = self.db.fetchall(
            """
            SELECT
                payment_method,
                COALESCE(SUM(total), 0) as total,
                COUNT(*) as count
            FROM invoices
            WHERE DATE(created_at) BETWEEN DATE(?) AND DATE(?)
            AND status != 'returned'
            GROUP BY payment_method
            """,
            (start_date, end_date)
        )

        by_payment = {
            row['payment_method']: {
                'total': row['total'],
                'count': row['count']
            }
            for row in payment_rows
        }

        # Top products
        top_products = self.top_products(10, start_date, end_date)

        return PeriodReport(
            start_date=start_date,
            end_date=end_date,
            total_sales=total_sales,
            invoice_count=invoice_count,
            average_sale=round(average_sale, 2),
            daily_breakdown=daily_breakdown,
            top_products=top_products,
            by_payment_method=by_payment
        )

    def top_products(
        self,
        limit: int = 10,
        start_date: str = None,
        end_date: str = None
    ) -> list[TopProduct]:
        """
        Get top selling products.

        Args:
            limit: Maximum number of products to return
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of top products by quantity sold
        """
        if start_date and end_date:
            rows = self.db.fetchall(
                """
                SELECT
                    ii.product_id,
                    ii.product_name,
                    SUM(ii.quantity) as quantity_sold,
                    SUM(ii.line_total) as revenue
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE DATE(i.created_at) BETWEEN DATE(?) AND DATE(?)
                AND i.status != 'returned'
                AND ii.return_status = 'none'
                GROUP BY ii.product_id, ii.product_name
                ORDER BY quantity_sold DESC
                LIMIT ?
                """,
                (start_date, end_date, limit)
            )
        else:
            rows = self.db.fetchall(
                """
                SELECT
                    ii.product_id,
                    ii.product_name,
                    SUM(ii.quantity) as quantity_sold,
                    SUM(ii.line_total) as revenue
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE i.status != 'returned'
                AND ii.return_status = 'none'
                GROUP BY ii.product_id, ii.product_name
                ORDER BY quantity_sold DESC
                LIMIT ?
                """,
                (limit,)
            )

        return [
            TopProduct(
                product_id=row['product_id'],
                product_name=row['product_name'],
                quantity_sold=row['quantity_sold'],
                revenue=row['revenue']
            )
            for row in rows
        ]

    def export_csv(
        self,
        report_type: str,
        params: dict = None,
        output_path: str = None
    ) -> str:
        """
        Export report data to CSV.

        Args:
            report_type: Type of report ('daily', 'period', 'top_products')
            params: Report parameters (date, start_date, end_date, limit)
            output_path: Optional path to save CSV file

        Returns:
            CSV content as string, or file path if output_path specified
        """
        params = params or {}

        if report_type == 'daily':
            date = params.get('date', datetime.now().strftime('%Y-%m-%d'))
            report = self.daily_sales(date)
            headers = ['Date', 'Total Sales', 'Invoice Count', 'Average Sale']
            rows = [[report.date, report.total_sales, report.invoice_count, report.average_sale]]

        elif report_type == 'period':
            start = params.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
            end = params.get('end_date', datetime.now().strftime('%Y-%m-%d'))
            report = self.period_sales(start, end)

            headers = ['Date', 'Total Sales', 'Invoice Count', 'Average Sale']
            rows = [
                [d.date, d.total_sales, d.invoice_count, d.average_sale]
                for d in report.daily_breakdown
            ]
            # Add totals row
            rows.append(['TOTAL', report.total_sales, report.invoice_count, report.average_sale])

        elif report_type == 'top_products':
            limit = params.get('limit', 10)
            start = params.get('start_date')
            end = params.get('end_date')
            products = self.top_products(limit, start, end)

            headers = ['Product ID', 'Product Name', 'Quantity Sold', 'Revenue']
            rows = [
                [p.product_id, p.product_name, p.quantity_sold, p.revenue]
                for p in products
            ]

        else:
            raise ValueError(f"Unknown report type: {report_type}")

        # Generate CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        csv_content = output.getvalue()

        if output_path:
            path = Path(output_path)
            path.write_text(csv_content)
            return str(path)

        return csv_content

    def get_today_summary(self) -> dict:
        """Get quick summary for today."""
        today = datetime.now().strftime('%Y-%m-%d')
        daily = self.daily_sales(today)
        return daily.to_dict()
