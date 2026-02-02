import { API_BASE } from "../ui/api";

export const downloadFile = async (path: string, filename: string, token: string | null) => {
    const headers: Record<string, string> = {};
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${path}`, { headers });
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
};