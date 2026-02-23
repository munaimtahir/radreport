/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../Dashboard';
import * as authHook from '../../ui/auth';
import * as apiModule from '../../ui/api';

vi.mock('../../ui/auth', () => ({
    useAuth: vi.fn(),
}));

vi.mock('../../ui/api', () => ({
    apiGet: vi.fn(),
}));

const renderWithRouter = (ui: React.ReactElement) => {
    return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('Dashboard component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (authHook.useAuth as any).mockReturnValue({
            token: 'fake-token',
            user: { username: 'testuser', groups: [] }
        });
    });

    it('renders loading state initially', () => {
        (apiModule.apiGet as any).mockImplementation(() => new Promise(() => { }));
        renderWithRouter(<Dashboard />);
        expect(screen.getByText('Loading...')).toBeDefined();
    });

    it('displays canonical dashboard data when API succeeds', async () => {
        const mockData = {
            timestamp_generated: '2026-02-23T00:00:00Z',
            timezone_used: 'Asia/Karachi',
            tenant_id: null,
            user_context: { username: 'testuser', is_admin: false, scope: 'my' },
            metrics: [
                { key: 'total_patients_today', label: 'Test Total Patients', value: 42, definition: 'A definition' },
            ],
            sections: {
                pending_worklist: { items: [], total_items: 0, scope: 'my', grouped_by_department: null },
                flow: {
                    registered_count: 10,
                    paid_count: 8,
                    performed_count: 5,
                    reported_count: 3,
                    verified_count: 1
                }
            }
        };

        (apiModule.apiGet as any).mockImplementation((url: string) => {
            if (url === '/dashboard/summary/') return Promise.resolve(mockData);
            if (url === '/health/') return Promise.resolve({ status: 'ok', latency_ms: 10, checks: { db: 'ok' } });
            return Promise.reject(new Error('not found'));
        });

        renderWithRouter(<Dashboard />);

        await waitFor(() => {
            expect(screen.getByText('Test Total Patients')).toBeDefined();
        });

        expect(screen.getByText('42')).toBeDefined();
        expect(screen.getByText(/Timezone: Asia\/Karachi/)).toBeDefined();
    });

    it('displays error state when API fails', async () => {
        (apiModule.apiGet as any).mockImplementation((url: string) => {
            if (url === '/dashboard/summary/') return Promise.reject(new Error('Network error'));
            return Promise.resolve({});
        });

        renderWithRouter(<Dashboard />);

        await waitFor(() => {
            expect(screen.getByText('Network error')).toBeDefined();
        });
    });
});
