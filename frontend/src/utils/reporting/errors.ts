export function resolveReportingErrorMessage(error: any): string {
  const detail = error?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.code === "no_active_template") {
    return "No active template configured for this service";
  }
  if (detail?.message) return detail.message;
  return error?.message || "Failed to load report data";
}
