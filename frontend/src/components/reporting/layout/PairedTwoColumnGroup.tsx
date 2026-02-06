import React, { ReactNode } from "react";
import { theme } from "../../../theme";

interface PairedTwoColumnGroupProps {
    title: string;
    rightTitle: string;
    leftTitle: string;
    rightContent: ReactNode;
    leftContent: ReactNode;
    compact?: boolean;
}

export default function PairedTwoColumnGroup({
    title,
    rightTitle,
    leftTitle,
    rightContent,
    leftContent,
    compact
}: PairedTwoColumnGroupProps) {
    return (
        <div data-testid={`paired-group-${title.toLowerCase().replace(/\s+/g, "-")}`} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ fontWeight: 600, color: theme.colors.textPrimary, borderBottom: `1px solid ${theme.colors.borderLight}`, paddingBottom: 8 }}>
                {title}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                <div data-testid="paired-group-right-column" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: theme.colors.textSecondary, textTransform: "uppercase" }}>
                        {rightTitle}
                    </div>
                    {rightContent}
                </div>
                <div data-testid="paired-group-left-column" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: theme.colors.textSecondary, textTransform: "uppercase" }}>
                        {leftTitle}
                    </div>
                    {leftContent}
                </div>
            </div>
        </div>
    );
}
