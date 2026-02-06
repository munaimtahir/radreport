import React from "react";
import { theme } from "../../../theme";

interface MeasurementInputProps {
    value: number | string | undefined | null;
    onChange: (val: number | "") => void;
    unit: string;
    disabled?: boolean;
}

export default function MeasurementInput({
    value,
    onChange,
    unit,
    disabled
}: MeasurementInputProps) {
    return (
        <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
            <input
                type="number"
                value={value ?? ""}
                onChange={(e) => {
                    const val = e.target.value;
                    onChange(val === "" ? "" : Number(val));
                }}
                disabled={disabled}
                style={{
                    width: "100%",
                    padding: "10px 12px",
                    paddingRight: 40,
                    borderRadius: 8,
                    border: `1px solid ${theme.colors.border}`,
                    fontSize: 14,
                    fontFamily: "inherit",
                    backgroundColor: disabled ? theme.colors.backgroundGray : "white",
                }}
            />
            <span
                data-testid="measurement-unit-badge"
                style={{
                    position: "absolute",
                    right: 12,
                    color: theme.colors.textTertiary,
                    fontSize: 12,
                    fontWeight: 500,
                    pointerEvents: "none"
                }}
            >
                {unit}
            </span>
        </div>
    );
}
