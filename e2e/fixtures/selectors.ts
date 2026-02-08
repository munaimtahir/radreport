export const SELECTORS = {
  login: {
    username: '[data-testid="login-username"]',
    password: '[data-testid="login-password"]',
    submit: '[data-testid="login-submit"]',
  },
  worklist: {
    search: '[data-testid="worklist-search"]',
    tableRow: (id: string) => `[data-testid="workitem-row-${id}"]`,
    openReport: '[data-testid="open-report"]',
  },
  report: {
    title: '[data-testid="report-title"]',
    save: '[data-testid="report-save"]',
    publish: '[data-testid="report-publish"]',
    status: '[data-testid="report-status"]',
    preview: '[data-testid="report-preview"]',
    v2Marker: '[data-testid="v2-report-ui"]',
    field: (key: string) => `[data-testid="field-${key}"]`,
  },
};
