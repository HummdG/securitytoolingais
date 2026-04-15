from dataclasses import dataclass, field
from typing import Optional

TOOLS = [
    "XSIAM SIEM", "XSIAM XDR", "Prisma Access", "Firewalls", "PKI",
    "XSIAM Cloud", "ServiceNow", "XSIAM ASM", "IDAM Verify Access",
    "IDAM Verify Directory", "IDAM Verify Governance", "IDAM Verify Privilege",
    "QRadar SIEM", "Tenable",
]

MATURITY_LABELS = {
    0: "Not Started",
    1: "Service Implemented",
    2: "Policy / Integration",
    3: "Design & Monitoring",
    4: "Operational & KT Done",
    5: "Fully Operational",
}

# Status values found in the workbook
STATUS_ORDER = ["Complete", "In Progress", "Pending", "TBC", "N/A"]

STATUS_COLORS = {
    "Complete":    "#22c55e",
    "In Progress": "#f59e0b",
    "Pending":     "#ef4444",
    "TBC":         "#8b5cf6",
    "N/A":         "#94a3b8",
}

MATURITY_COLORS = {
    0: "#ef4444",
    1: "#f97316",
    2: "#eab308",
    3: "#22d3ee",
    4: "#3b82f6",
    5: "#22c55e",
}


@dataclass
class ChecklistItem:
    maturity_level: int   # 1–5
    item_name: str


@dataclass
class ToolTask:
    tool: str
    item: ChecklistItem
    applicable: str        # "Y" or "N"
    status: str            # Complete / In Progress / Pending / TBC / N/A
    comment: Optional[str]


@dataclass
class ToolSummary:
    tool: str
    current_maturity: int  # 0–5 from Maturity Summary sheet
    pct_complete: float    # 0–100 from % Complete sheet
    tasks: list = field(default_factory=list)  # list[ToolTask]
