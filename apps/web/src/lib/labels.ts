const STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft ready",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  SIMULATED_SENT: "Mock send done",
  COMPLETED: "Done",
  RUNNING: "In progress",
  PENDING: "Waiting",
  WAITING_FOR_APPROVAL: "Needs your review",
  FAILED: "Failed",
  BLOCKED: "Blocked",
  PASSED: "Cleared to contact",
  NONE: "No message",
  ACTIVE: "Active",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
  STANDARD: "Standard",
  GOLD: "Gold",
  PREMIUM: "Premium",
  PRIVATE: "Private",
};

const KPI_LABELS: Record<string, string> = {
  aiCampaigns: "Campaigns created",
  customersAnalysed: "Customers in database",
  pendingApprovals: "Messages waiting for you",
  approvedMessages: "Messages approved",
  complianceBlocks: "Compliance blocks",
  simulatedMessagesSent: "Mock WhatsApp sends",
};

const AGENT_LABELS: Record<string, string> = {
  IntentUnderstandingAgent: "1. Understand request",
  CustomerRetrievalAgent: "2. Find customers",
  CustomerValueAgent: "3. Score customer value",
  ConversionPropensityAgent: "4. Score conversion chance",
  ProductRecommendationAgent: "5. Recommend product",
  EligibilityAgent: "6. Check eligibility",
  ConsentComplianceAgent: "7. Check consent & compliance",
  MessageGenerationAgent: "8. Draft WhatsApp message",
  ExplainabilityAgent: "9. Prepare explanations",
  HumanApproval: "10. Waiting for your approval",
};

const ROLE_LABELS: Record<string, string> = {
  RELATIONSHIP_MANAGER: "Relationship Manager",
  SUPERVISOR: "Supervisor",
  ADMIN: "Admin",
};

export function friendlyStatus(value?: string | null): string {
  if (!value) return "—";
  return (
    STATUS_LABELS[value] ||
    value
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/^\w/, (c: string) => c.toUpperCase())
  );
}

export function friendlyKpi(key: string): string {
  return KPI_LABELS[key] || key;
}

export function friendlyAgent(name?: string | null): string {
  if (!name) return "Agent step";
  return AGENT_LABELS[name] || name.replace(/([A-Z])/g, " $1").trim();
}

export function friendlyRole(role?: string | null): string {
  if (!role) return "";
  return ROLE_LABELS[role] || role;
}

export function actionLabelForResult(row: {
  contactAllowed: boolean;
  messageStatus?: string;
}): string {
  if (!row.contactAllowed) return "View why blocked";
  if (row.messageStatus === "SIMULATED_SENT") return "View sent message";
  if (row.messageStatus === "APPROVED") return "Send mock WhatsApp";
  if (row.messageStatus === "DRAFT") return "Review & approve";
  return "Open customer";
}
