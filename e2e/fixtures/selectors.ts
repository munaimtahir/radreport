export const selectors = {
  loginUsername: 'login-username',
  loginPassword: 'login-password',
  loginSubmit: 'login-submit',
  reportingRoot: 'reporting-v2',
  reportTemplateCode: 'report-template-code',
  reportTemplateName: 'report-template-name',
  reportStatus: 'report-status',
  reportSave: 'report-save',
  reportSubmit: 'report-submit',
  reportSubmitConfirm: 'submit-confirm',
  reportVerify: 'report-verify',
  reportPublish: 'report-publish',
  reportPublishConfirm: 'publish-confirm',
  reportPublishConfirmButton: 'publish-confirm-button',
  reportPublishNotes: 'publish-notes',
  reportPreview: 'report-preview',
  reportSuccess: 'report-success',
  publishHistory: 'publish-history',
  reportingWorklist: 'reporting-worklist',
  worklistTable: 'worklist-table',
};

export const fieldTestId = (key: string) => `field-${key}`;
export const workitemRowTestId = (id: string) => `workitem-row-${id}`;
export const openReportTestId = (id: string) => `open-report-${id}`;
