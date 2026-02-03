# Phase-3C Template Builder Smoke Test

This document outlines the steps to manually test the core functionality of the Template V2 Builder, specifically focusing on the features implemented in Phase-3C.

## 1. Create New TemplateV2

1.  Navigate to **Settings > Templates V2**.
2.  Click **+ New Template**.
3.  Fill in the form:
    *   **Name**: `SMOKE_TEST_TPL`
    *   **Code**: `SMOKE_TEST_TPL_v1`
    *   **Modality**: `US`
4.  Click **Create**.
5.  You should be redirected to the **Template Builder** for `SMOKE_TEST_TPL_v1` at `/settings/templates-v2/{id}/builder`. (This redirect is now automatic.)

**Expected Outcome:** A new, empty template is created and the builder is displayed.

## 2. Add Sections & Fields

1.  In the **Sections** panel, click **+ Add Section**.
2.  Rename the new section to `Patient Info`.
3.  With the `Patient Info` section selected, in the **Fields** panel, click **+ Add Field** twice.
4.  Edit the new fields:
    *   Field 1:
        *   **Title**: `Patient Name`
        *   **Key**: `patient_name`
    *   Field 2:
        *   **Title**: `Patient Age`
        *   **Key**: `patient_age`
5.  Add another section named `Findings`.
6.  Add a field to the `Findings` section:
    *   **Title**: `Main Finding`
    *   **Key**: `main_finding`
    *   **Type**: `text`

**Expected Outcome:** The builder state should reflect the new sections and fields. The Live Preview panel should show the updated JSON schema.

## 3. Add Narrative Rules

1.  Switch to the **Narrative Logic** tab.
2.  In the **Narrative Sections** panel, click **+ Add Narrative Section**.
3.  Rename the new section to `Patient Details`.
4.  Add a text line: `Patient: {{patient_name}}, Age: {{patient_age}}`.
5.  Add another narrative section named `Report Findings`.
6.  Add a conditional line:
    *   **IF** `main_finding` `is_not_empty`
    *   **THEN** (text): `The main finding is: {{main_finding}}`.

**Expected Outcome:** The narrative rules are added and configured correctly.

## 4. Insert Block (with Conflict Resolution)

1.  Switch back to the **Form Design** tab.
2.  Click **Insert Block**.
3.  A modal should appear with a list of available blocks.
4.  Assuming a block with a conflicting key exists (e.g., a block with a field with key `patient_name`), select it for insertion.
5.  A conflict resolution modal should appear, listing `patient_name` as a conflict.
6.  In the input field for `patient_name`, enter `block_patient_name`.
7.  Click **Resolve and Insert**.
8.  **[If no conflicting block exists]** Select any block and click **Insert**.

**Expected Outcome:** The block's sections and fields are added to the template. If there was a conflict, the inserted field's key should be renamed to `block_patient_name`.

## 5. Freeze Template

1.  Click **Save Changes**.
2.  Go back to the **Templates V2** list.
3.  Find `SMOKE_TEST_TPL_v1` and click the **Freeze** action (row-level button).
4.  Confirm the action.
5.  Re-enter the builder for `SMOKE_TEST_TPL_v1` (use **Open Builder** in the same row).

**Expected Outcome:**
*   A banner at the top indicates "This template is frozen and cannot be edited."
*   All editing controls (adding/editing/deleting fields/sections/narratives) are disabled.
*   A **Duplicate as New Version** button is visible.

## 6. Duplicate Frozen Template

1.  In the frozen template builder, click **Duplicate as New Version**.

**Expected Outcome:**
*   You are redirected to a new template builder page.
*   The URL should reflect a new template ID and still end with `/builder`.
*   The template name should be `SMOKE_TEST_TPL` and the code should be `SMOKE_TEST_TPL_v2`.
*   The builder should be fully editable.
*   The new template has a `draft` status and `is_frozen` is `false`.

## 7. Activate and Map Template

1.  Save the new `SMOKE_TEST_TPL_v2` template.
2.  Go back to the **Templates V2** list.
3.  Activate `SMOKE_TEST_TPL_v2`.
4.  Navigate to **Settings > Service-Template Links** (in sidebar).
5.  Create a new link between a service (e.g., `US-ABD`) and the `SMOKE_TEST_TPL_v2` template.

**Expected Outcome:** The template is now active and linked to a service.

## 8. Confirm in Workflow

1.  Go to the **Reporting** page.
2.  Start a new report for the service linked in the previous step (e.g., `US-ABD`).
3.  The reporting form should appear.

**Expected Outcome:** The form rendered should match the schema of `SMOKE_TEST_TPL_v2`, including the fields from the inserted block. The narrative should be generated correctly based on the data entered.
