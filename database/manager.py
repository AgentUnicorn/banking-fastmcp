import sqlite3
from typing import Optional

from database.models import Account, Bank, SavedRecipient, Transaction


class BankingDatabase:
    def __init__(self, db_path: str = "banking.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Accounts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS banks (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                bin VARCHAR(20) UNIQUE NOT NULL,
                short_name VARCHAR(100) NOT NULL,
                created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
            );
        """
        )

        # Transactions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                email VARCHAR(50) UNIQUE NOT NULL,
                account_number BIGINT UNIQUE NOT NULL,
                account_name NVARCHAR(100) NOT NULL,
                balance DECIMAL(18,2) DEFAULT 0.00,
                currency VARCHAR(10) NOT NULL DEFAULT 'VND',
                created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
                updated_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP)
            );
        """
        )

        # Saved recipients table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                from_account_id INTEGER,
                to_account_id INTEGER,
                amount DECIMAL(18,2) NOT NULL,
                currency VARCHAR(10) DEFAULT 'VND',
                type VARCHAR(50),  -- transfer, deposit, withdrawal, etc.
                status VARCHAR(50) DEFAULT 'completed',
                description TEXT,
                date_issued TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
                created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
                FOREIGN KEY (from_account_id) REFERENCES accounts(id)
            );
        """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS saved_recipients (
                    id INTEGER PRIMARY KEY,
                    owner_account_id INTEGER,  -- Account that saved this recipient
                    account_number BIGINT NOT NULL,
                    account_name NVARCHAR(100) NOT NULL,
                    bank_id INTEGER,
                    created_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP),
                    FOREIGN KEY (owner_account_id) REFERENCES accounts(id),
                    FOREIGN KEY (bank_id) REFERENCES banks(id)
                );
        """
        )

        conn.commit()

        # Seed sample data if empty
        cursor.execute("SELECT COUNT(*) as count FROM accounts")
        if cursor.fetchone()["count"] == 0:
            self._seed_data(cursor)
            conn.commit()

        conn.close()

    def _seed_data(self, cursor):
        # Sample accounts
        cursor.execute(
            """
            INSERT INTO accounts (id, email, account_number, account_name, balance)
            VALUES 
                (1,'example@com.vn', '1234567890', 'Nguyễn Văn A', 500000000);
        """
        )

        cursor.execute(
            """
            INSERT INTO saved_recipients(owner_account_id, account_number, account_name, bank_id)
            VALUES
                (1, '1234567891', 'Nguyễn Phương Bình', 4);
            """
        )

    def get_accounts(self) -> list[Account]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, account_number, account_name, balance, currency, created_at, updated_at FROM accounts"
        )
        rows = cursor.fetchall()
        conn.close()
        return [Account(**dict(row)) for row in rows]

    def get_account_by_email(self, email: str) -> Account | None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, account_number, account_name, balance, currency, created_at, updated_at FROM accounts WHERE email = ?",
            (email,),
        )
        row = cursor.fetchone()
        conn.close()
        return Account(**dict(row)) if row else None

    def get_account_by_number(self, account_number: int) -> Account | None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, account_number, account_name, balance, currency, created_at, updated_at FROM accounts WHERE account_number = ?",
            (account_number,),
        )
        row = cursor.fetchone()
        conn.close()
        return Account(**dict(row)) if row else None

    def get_transactions(
        self, account_number: int, limit: int = 10
    ) -> list[Transaction]:
        conn = self.get_connection()
        cursor = conn.cursor()

        # Find account ID first
        cursor.execute(
            "SELECT id FROM accounts WHERE account_number = ?", (account_number,)
        )
        acc = cursor.fetchone()
        if not acc:
            conn.close()
            return []

        account_id = acc["id"]

        # Get transactions where the account is sender or receiver
        cursor.execute(
            """
            SELECT id, from_account_id, to_account_id, amount, currency, type, status, description, date_issued, created_at
            FROM transactions
            WHERE from_account_id = ? OR to_account_id = ?
            ORDER BY date_issued DESC
            LIMIT ?
            """,
            (account_id, account_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()
        return [Transaction(**dict(row)) for row in rows]

    def transfer_money(
        self,
        from_account_number: int,
        to_account_number: int,
        amount: float,
        description: str,
    ) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Get sender and receiver
            cursor.execute(
                "SELECT id, balance FROM accounts WHERE account_number = ?",
                (from_account_number,),
            )
            sender = cursor.fetchone()

            cursor.execute(
                "SELECT id FROM saved_recipients WHERE account_number = ?",
                (to_account_number,),
            )
            receiver = cursor.fetchone()

            if not sender or not receiver:
                raise ValueError(
                    f"Invalid account(s): {from_account_number if not sender else to_account_number}"
                )

            if sender["balance"] < amount:
                raise ValueError("Insufficient balance")

            # Perform transfer
            cursor.execute(
                "UPDATE accounts SET balance = balance - ? WHERE account_number = ?",
                (amount, from_account_number),
            )
            cursor.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (amount, receiver["id"]),
            )

            # Record transaction
            cursor.execute(
                """
                INSERT INTO transactions (from_account_id, to_account_id, amount, currency, type, status, description)
                VALUES (?, ?, ?, 'VND', 'transfer', 'completed', ?)
                """,
                (sender["id"], receiver["id"], amount, description),
            )

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_saved_recipients(self, owner_account_id: int) -> list[SavedRecipient]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sr.id, sr.owner_account_id, sr.account_number, sr.account_name, sr.bank_id, b.short_name as bank_name, sr.created_at
            FROM saved_recipients as sr 
            LEFT JOIN banks as b
            WHERE b.id = sr.bank_id AND owner_account_id = ?
            """,
            (owner_account_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [SavedRecipient(**dict(row)) for row in rows]

    def get_saved_recipient(
        self, owner_account_id: int, account_number: int
    ) -> SavedRecipient | None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sr.id, sr.owner_account_id, sr.account_number, sr.account_name, sr.bank_id, b.short_name as bank_name, sr.created_at
            FROM saved_recipients as sr 
            LEFT JOIN banks as b
            WHERE b.id = sr.bank_id AND owner_account_id = ? AND sr.account_number = ?
            """,
            (owner_account_id, account_number),
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return SavedRecipient(**dict(row))

    def add_saved_recipient(
        self,
        owner_account_id: int,
        account_number: int,
        account_name: str,
        bank_id: int | None = None,
    ) -> SavedRecipient:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO saved_recipients (owner_account_id, account_number, account_name, bank_id)
            VALUES (?, ?, ?, ?)
            """,
            (owner_account_id, account_number, account_name, bank_id),
        )
        recipient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return SavedRecipient(
            id=recipient_id,
            owner_account_id=owner_account_id,
            account_number=account_number,
            account_name=account_name,
            bank_id=bank_id,
            bank_name=None,
        )

    def find_bank_by_name(self, bank_name: str) -> Bank | None:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECt * FROM banks
            WHERE name LIKE '%{bank_name}%' OR short_name LIKE '%{bank_name}%' OR code LIKE '%{bank_name}%'
            """
        )

        bank = cursor.fetchone()
        conn.close()
        if not bank:
            return None
        return Bank(**dict(bank))
