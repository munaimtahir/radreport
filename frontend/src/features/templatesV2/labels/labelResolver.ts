/**
 * labelResolver.ts
 * 
 * Deterministic label generation for Template V2 keys.
 * Hides raw snake_case keys from non-technical users.
 */

import { labelOverrides } from './labelOverrides';

export function resolveLabel(key: string, explicitLabel?: string): string {
    // 1. If explicit label provided in schema metadata, use it
    if (explicitLabel) return explicitLabel;

    // 2. Check manual overrides
    if (labelOverrides[key]) return labelOverrides[key];

    // 3. Fallback: Transform key
    // kid_r_length_cm -> Right kidney length (cm)
    // liv_echogenicity -> Liver echogenicity

    let label = key;

    // Handle _r_ and _l_ patterns
    label = label.replace(/_r_/g, ' (Right) ');
    label = label.replace(/_l_/g, ' (Left) ');

    // Replace underscores with spaces
    label = label.replace(/_/g, ' ');

    // Capitalize first letter
    label = label.charAt(0).toUpperCase() + label.slice(1);

    // Clean up double spaces or trailing spaces from replacements
    label = label.replace(/\s+/g, ' ').trim();

    // Move (Right)/(Left) to the front if they exist for better readability
    if (label.includes('(Right)')) {
        label = 'Right ' + label.replace('(Right)', '').trim();
    }
    if (label.includes('(Left)')) {
        label = 'Left ' + label.replace('(Left)', '').trim();
    }

    return label;
}

export function formatUnit(key: string): string | null {
    if (key.endsWith('_cm')) return 'cm';
    if (key.endsWith('_mm')) return 'mm';
    if (key.endsWith('_cc')) return 'cc';
    if (key.endsWith('_g')) return 'g';
    return null;
}
