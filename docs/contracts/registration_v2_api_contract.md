# Registration v2 API Contract

## Endpoints

### 1. GET /api/services/most-used/
**Description**: Returns top services by usage count (based on ServiceVisitItem and OrderItem records).

**Query Parameters**:
- `limit` (optional, default: 5): Number of services to return

**Response**:
```json
[
  {
    "id": "uuid",
    "code": "USG-001",
    "name": "Ultrasound Abdomen",
    "price": 1500.00,
    "charges": 1500.00,
    "category": "Radiology",
    "modality": {
      "id": "uuid",
      "code": "USG",
      "name": "Ultrasound"
    },
    "is_active": true,
    "usage_count": 42
  }
]
```

**Notes**:
- `usage_count` is calculated from ServiceVisitItem (workflow) + OrderItem (legacy) counts
- Services are sorted by usage_count descending
- Only active services are returned
- If no usage data exists, returns empty array (frontend should have local fallback)

---

### 2. POST /api/workflow/visits/create_visit/
**Description**: Creates a service visit with multiple services and billing information.

**Request Payload**:
```json
{
  "patient_id": "uuid",  // Required if not creating new patient
  // OR patient fields (if creating new):
  "name": "string",  // Required if no patient_id
  "age": 30,  // Optional
  "date_of_birth": "YYYY-MM-DD",  // Optional
  "gender": "Male|Female|Other",  // Optional
  "phone": "string",  // Optional
  "address": "string",  // Optional
  
  // Services (required):
  "service_ids": ["uuid1", "uuid2"],  // Required: list of service UUIDs
  
  // Billing (required):
  "subtotal": "10.00",  // Decimal, required
  "discount": "2.00",  // Decimal, discount amount (default: 0)
  "discount_percentage": "20.00",  // Decimal, optional: discount percentage (0-100)
  "total_amount": "10.00",  // Decimal, required
  "net_amount": "8.00",  // Decimal, optional: calculated if not provided
  "amount_paid": "8.00",  // Decimal, required
  "payment_method": "cash|card|online|insurance|other"  // Required, default: "cash"
}
```

**Response**:
```json
{
  "id": "uuid",
  "visit_id": "240107-001",
  "patient": {
    "id": "uuid",
    "name": "John Doe",
    "mrn": "MRN-001"
  },
  "status": "REGISTERED",
  "registered_at": "2024-01-07T12:00:00Z"
}
```

**Validation Rules**:
- Either `patient_id` OR `name` must be provided
- Either `service_ids` (list) OR `service_id` (legacy single) must be provided
- All services must exist and be active
- `subtotal` should match sum of service prices
- `net_amount = subtotal - discount`
- If `discount_percentage` is provided, backend calculates `discount = subtotal * (discount_percentage / 100)`

**Notes**:
- Frontend currently sends `discount` as amount (not percentage)
- Backend accepts both `discount` (amount) and `discount_percentage`
- If both provided, `discount` takes precedence

---

### 3. GET /api/pdf/{visit_id}/receipt/
**Description**: Generates receipt PDF for a service visit.

**Response**: PDF blob (Content-Type: application/pdf)

**Notes**:
- Requires authentication (Bearer token)
- Opens in new window/tab for printing
- PDF includes header_text, footer_text, logo, patient info, services, billing summary

---

### 4. GET /api/receipt-settings/
**Description**: Get receipt branding settings (authenticated).

**Response**:
```json
{
  "header_text": "Consultants Clinic Place",
  "footer_text": "Thank you for your visit",
  "logo_image_url": "https://...",
  "header_image_url": "https://...",
  "updated_at": "2024-01-07T12:00:00Z"
}
```

---

### 5. PATCH /api/receipt-settings/1/
**Description**: Update receipt settings.

**Request Payload**:
```json
{
  "header_text": "string",  // Optional
  "footer_text": "string"   // Optional
}
```

**Response**: Updated settings object

---

## Frontend Payload Mapping

### Current RegistrationPage.tsx sends:
```json
{
  "patient_id": "uuid",
  "service_ids": ["uuid1", "uuid2"],
  "subtotal": 100.00,
  "total_amount": 100.00,
  "discount": 20.00,  // Amount, not percentage
  "net_amount": 80.00,
  "amount_paid": 80.00,
  "payment_method": "cash"
}
```

### Recommended (for discount %):
```json
{
  "patient_id": "uuid",
  "service_ids": ["uuid1", "uuid2"],
  "subtotal": 100.00,
  "total_amount": 100.00,
  "discount_percentage": 20.00,  // Percentage (0-100)
  "net_amount": 80.00,
  "amount_paid": 80.00,
  "payment_method": "cash"
}
```

**Note**: Backend accepts both formats. Frontend should send `discount_percentage` if user enters percentage, or `discount` if user enters amount.
