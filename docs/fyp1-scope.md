# StringSense FYP1 Scope

This document is the source of truth for the FYP1 demo scope. The FYP1 target is a smaller, backend-connected prototype that proves recommendation, booking, admin booking management, inventory, business hours, limited store settings, and booking photos/comments.

## FYP1 Included

### Player

- Register, login, forgot/reset password.
- View and edit player profile.
- Generate backend-backed string recommendations.
- View recommendation results and string details.
- Create a stringing booking from backend-generated slots.
- Upload an optional booking photo immediately after booking creation through a booking update. The booking remains created if the follow-up photo upload fails.
- View own booking list, booking detail, booking status, booking photos, and booking comments.

### Admin

- Login with backend admin authentication.
- View booking list and booking detail.
- Update booking status.
- Add booking-specific comments and optional photos.
- View inventory list and inventory detail.
- Update inventory price, stock level, availability, and shop note.
- Edit business hours, break windows, slot duration, capacity, and special closed dates.
- Edit limited store settings: store name, contact, address, support text, booking notes, and booking policy text.

### Backend

- Authentication and role guards.
- Player profile persistence.
- String catalog and inventory persistence.
- Baseline hybrid recommendation flow.
- Booking creation, listing, detail, status update, and status history.
- Booking update persistence for player/admin comments and photos.
- Local FYP upload storage under `backend/var/uploads/`.
- Business-hours-driven slot generation.
- Limited store settings persistence.

## FYP2 Deferred

These are not FYP1 deliverables and should not appear as completed demo features:

- Chat and admin support chat.
- Payment, wallet, and checkout.
- Notifications and notification preferences.
- Racket Passport and saved racket product module.
- QR check-in.
- Service queue.
- RAG chatbot as a main feature.
- Production collaborative filtering integration.
- Production deep learning ranking integration.
- Advanced analytics dashboard.
- Advanced admin settings beyond the limited FYP1 store settings listed above.

Route files for deferred modules may remain in the repo for future work, but primary navigation and demo CTAs should not present them as completed FYP1 functionality.

## Recommendation Positioning

For FYP1, describe the recommender as:

> A baseline hybrid recommendation module using rule-based logic and content-based attribute matching, enhanced by structured string features and review-derived item knowledge.

Do not claim that FYP1 has deployed collaborative filtering, deep learning ranking, or RAG-based recommendation assistance.

## FYP1 Demo Proof

- Player can create a booking using a backend-generated slot.
- Player can attach a booking photo through the follow-up booking update endpoint.
- Booking persists in the backend database.
- Admin can retrieve the booking.
- Admin can add a booking comment/photo.
- Player can view admin booking comments/photos.
- Admin can update booking status.
- Player can see the updated status.
- Admin inventory, business-hours, and limited store-settings updates persist.
