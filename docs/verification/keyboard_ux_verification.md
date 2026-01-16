# Keyboard UX Edge Cases Verification

## Manual Testing Checklist

### ✅ Textarea Behavior
- [ ] **Address field**: Press Enter → Focus moves to next field (not newline)
- [ ] **Shift+Enter**: Creates newline (normal behavior preserved)
- [ ] **Tab key**: Still works normally

**Expected**: Enter = Tab, Shift+Enter = newline

---

### ✅ Dropdown Behavior

#### Patient Search Dropdown
- [ ] **Arrow Down**: Moves selection down
- [ ] **Arrow Up**: Moves selection up
- [ ] **Enter**: Selects highlighted patient
- [ ] **Escape**: Closes dropdown
- [ ] **Click outside**: Closes dropdown

#### Service Search Dropdown
- [ ] **Arrow Down**: Moves selection down
- [ ] **Arrow Up**: Moves selection up
- [ ] **Enter**: Adds service to selection
- [ ] **Escape**: Closes dropdown
- [ ] **Mouse hover**: Updates selection index

---

### ✅ Focus Transitions

#### Patient Form Flow
1. Name → Enter → Age
2. Age → Enter → DOB
3. DOB → Enter → Gender
4. Gender → Enter → Phone
5. Phone → Enter → Address
6. Address → Enter → Next focusable element

**Expected**: Each Enter moves focus to next field in logical order

#### Service Section Flow
1. Service Search → Enter → Discount field
2. Discount → Enter → Amount Paid
3. Amount Paid → Enter → Payment Method

**Expected**: Smooth focus transitions without skipping fields

---

### ✅ Remove Button Focus Handling
- [ ] **Click Remove**: Focus returns to service search
- [ ] **Keyboard navigation**: Remove buttons are focusable
- [ ] **Tab order**: Remove buttons are in logical tab sequence

---

### ✅ Mobile Search Debounce
- [ ] **Type "ultra"**: Wait 300ms → Dropdown appears
- [ ] **Type quickly**: Only last search triggers API call
- [ ] **Clear search**: Dropdown disappears immediately

**Expected**: Debounce prevents excessive API calls

---

### ✅ Edge Cases

#### Empty States
- [ ] **No services selected**: Discount field disabled or hidden
- [ ] **No patient selected**: Service section hidden
- [ ] **Empty search**: Dropdown shows "No results"

#### Error States
- [ ] **API error**: Error message displayed, focus not lost
- [ ] **Invalid discount**: Value clamped, error shown
- [ ] **Network timeout**: Graceful degradation

#### Accessibility
- [ ] **Screen reader**: All fields have labels
- [ ] **Keyboard only**: Full flow possible without mouse
- [ ] **Focus indicators**: Visible focus rings on all interactive elements

---

## Automated Verification

Run E2E tests:
```bash
npx playwright test tests/e2e/registration_v2.spec.ts -g "Keyboard"
```

## Browser Compatibility

Test in:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari (WebKit)

## Known Issues

None currently. Report any issues in the verification results.
