export function resolveReportingErrorMessage(error: any): string {
  const detail = error?.detail;
  if (typeof detail === "string") return detail;

  const detailCode = detail?.code || detail?.error;
  if (detailCode === "no_active_template" || detailCode === "NO_ACTIVE_V2_TEMPLATE") {
    return "No active template configured for this service";
  }

  if (detail?.message) return detail.message;
  return error?.message || "Failed to load report data";
}
