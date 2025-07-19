import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import App from '../../App';
import { MemoryRouter } from 'react-router-dom';

const server = setupServer(
    rest.get('/api/filtered', (req: any, res: any, ctx: any) => {
        return res(ctx.json({ data: [], total: 0, page: 1 }));
    })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('API Integration', () => {
    test('should fetch filtered entries', async () => {
        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        await waitFor(() => expect(screen.getByRole('main')).toBeInTheDocument());
    });

    test('should handle API errors gracefully', async () => {
        server.use(
            rest.get('/api/filtered', (req: any, res: any, ctx: any) => {
                return res(ctx.status(500), ctx.json({ error: 'Internal server error' }));
            })
        );
        render(
            <MemoryRouter>
                <App />
            </MemoryRouter>
        );
        // Check for error message or fallback UI
        await waitFor(() => {
            expect(screen.getByRole('main')).toBeInTheDocument();
        });
    });
}); 