import React from "react";
import { Link, useLocation } from "react-router-dom";
import { theme } from "../../theme";

interface NavLinkProps {
  to: string;
  children: React.ReactNode;
}

export default function NavLink({ to, children }: NavLinkProps) {
  const location = useLocation();
  
  // Determine if the link is active
  const isActive = to === "/" 
    ? location.pathname === "/" 
    : location.pathname.startsWith(to);

  return (
    <Link
      to={to}
      style={{
        padding: "10px 12px",
        textDecoration: "none",
        color: isActive ? theme.colors.brandBlue : theme.colors.textSecondary,
        backgroundColor: isActive ? theme.colors.brandBlueSoft : "transparent",
        borderRadius: theme.radius.base,
        fontSize: 14,
        fontWeight: isActive ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
        transition: theme.transitions.fast,
      }}
    >
      {children}
    </Link>
  );
}
