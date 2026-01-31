// frontend/src/utils/download.ts
import { API_BASE } from "../ui/api";

export const downloadFile = async (urlPath: string, filename: string, token: string) => {
  if (!token) {
    throw new Error("Authentication token is missing.");
  }
  try {
    const response = await fetch(`${API_BASE}${urlPath}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Download failed");
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (e: any) {
    // Re-throw original error if it exists, otherwise create a new one
    if (e instanceof Error) {
      throw e;
    }
    throw new Error(e?.message || "Download failed");
  }
};
