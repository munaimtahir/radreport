import React from "react";
import { theme } from "../../../theme";

interface SegmentedBooleanProps {
    value: boolean | undefined | null;
    onChange: (val: boolean) => void;
    disabled?: boolean;
    trueLabel?: string;
    falseLabel?: string;
}

export default function SegmentedBoolean({
    value,
    onChange,
    disabled,
    trueLabel = "Yes",
    falseLabel = "No"
}: SegmentedBooleanProps) {
    const isTrue = value === true;
    const isFalse = value === false;

    const buttonStyle = (active: boolean): React.CSSProperties => ({
        flex: 1,
        border: `1px solid ${active ? theme.colors.brandBlue : theme.colors.border}`,
        backgroundColor: active ? theme.colors.brandBlueSoft : "white",
        color: active ? theme.colors.brandBlueDark : theme.colors.textPrimary,
        fontWeight: active ? 600 : 400,
        padding: "8px 12px",
        cursor: disabled ? "not-allowed" : "pointer",
        textAlign: "center",
        transition: theme.transitions.fast,
        fontSize: theme.typography.fontSize.base,
    });

    return (
        <div style={{ display: "flex", borderRadius: theme.radius.md, overflow: "hidden", border: `1px solid ${theme.colors.border}` }}>
            <div
                style={buttonStyle(isTrue)}
                onClick={() => !disabled && onChange(true)}
            >
                {trueLabel}
            </div>
            <div
                style={{ width: 1, backgroundColor: theme.colors.border }}
            />
            <div
                style={buttonStyle(isFalse)}
                onClick={() => !disabled && onChange(false)}
            >
                {falseLabel}
            </div>
        </div>
    );
}
