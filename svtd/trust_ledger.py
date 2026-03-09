# Copyright 2026 The SVTD Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SVTD Trust Ledger - SQLite-based storage for trust weights and correction events.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

class TrustLedger:
    """SQLite-based ledger for persisting trust weights."""
    
    def __init__(self, db_path: str = "svtd_trust.db"):
        """
        Initialize the TrustLedger.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._conn = self._get_connection()
        self._init_db()
        
    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
        
    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _init_db(self):
        """Create tables if they don't exist."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS trust_weights (
                memory_id TEXT NOT NULL,
                client_id TEXT NOT NULL,
                trust_weight REAL DEFAULT 1.0,
                feedback_count INTEGER DEFAULT 0,
                is_cold BOOLEAN DEFAULT 0,
                last_feedback TEXT,
                decay_reason TEXT,
                corrected_by TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (memory_id, client_id)
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tw_client ON trust_weights (client_id)")
        self._conn.commit()

    def get_trust_weight(self, memory_id: str, client_id: str = "default") -> float:
        """
        Retrieve trust weight for a specific memory.
        
        Args:
            memory_id: The ID of the memory chunk.
            client_id: The client/user identifier.
            
        Returns:
            The trust weight (defaults to 1.0 if not found).
        """
        cursor = self._conn.execute(
            "SELECT trust_weight FROM trust_weights WHERE memory_id = ? AND client_id = ?",
            (memory_id, client_id)
        )
        row = cursor.fetchone()
        return row[0] if row else 1.0

    def update_trust_weight(self, memory_id: str, weight: float, client_id: str = "default", 
                           reason: Optional[str] = None, corrected_by: Optional[str] = None):
        """
        Update trust weight for a memory.
        
        Args:
            memory_id: The ID of the memory chunk.
            weight: The new trust weight.
            client_id: The client/user identifier.
            reason: Optional reason for the update (e.g., "decay", "correction").
            corrected_by: Optional ID of the memory that corrects this one.
        """
        now = datetime.now(timezone.utc).isoformat()
        is_cold = 1 if weight < 0.2 else 0
        
        # Check if exists
        cursor = self._conn.execute(
            "SELECT feedback_count FROM trust_weights WHERE memory_id = ? AND client_id = ?",
            (memory_id, client_id)
        )
        row = cursor.fetchone()
        
        if row:
            count = row[0] + 1
            self._conn.execute("""
                UPDATE trust_weights SET 
                    trust_weight = ?, 
                    feedback_count = ?, 
                    is_cold = ?, 
                    last_feedback = ?, 
                    decay_reason = ?, 
                    corrected_by = ?,
                    updated_at = ?
                WHERE memory_id = ? AND client_id = ?
            """, (weight, count, is_cold, now, reason, corrected_by, now, memory_id, client_id))
        else:
            self._conn.execute("""
                INSERT INTO trust_weights 
                (memory_id, client_id, trust_weight, feedback_count, is_cold, last_feedback, decay_reason, corrected_by, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (memory_id, client_id, weight, 1, is_cold, now, reason, corrected_by, now))
        self._conn.commit()

    def load_all_weights(self, client_id: Optional[str] = None) -> Dict[str, float]:
        """
        Load all trust weights into memory for fast lookup.
        
        Args:
            client_id: Optional client ID to filter by.
            
        Returns:
            Dict mapping memory_id to trust_weight.
        """
        query = "SELECT memory_id, trust_weight FROM trust_weights"
        params = []
        if client_id:
            query += " WHERE client_id = ?"
            params.append(client_id)
            
        cursor = self._conn.execute(query, params)
        return {row[0]: row[1] for row in cursor.fetchall()}
