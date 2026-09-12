# Society Management Service – Enterprise User Onboarding & Authentication Architecture

## Version

v1.0

## Objective

Build a **multi-tenant Society Management SaaS** where:

* A single application serves thousands of societies.
* Every society is completely isolated from every other society.
* Society administrators can configure and manage their own society.
* Residents can securely join their respective society.
* The platform requires minimal manual work after onboarding.
* The onboarding, authentication, authorization, and subscription systems are independent.

---

# High Level Architecture

```
                        Internet
                            │
                            ▼
                abcsocietymanagement.com
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
   Register Society                        Login
        │                                       │
        ▼                                       ▼
Platform Onboarding                     Authentication
        │                                       │
        ▼                                       ▼
 Society Provisioning              Identity + Membership
```

---

# Core Design Principles

## 1. Identity

Identity answers:

> Who is this user?

Examples:

* Email
* Password Hash
* Mobile Number
* MFA Settings

Identity is global.

A user may belong to one or many societies.

---

## 2. Membership

Membership answers:

> Which society does the user belong to?

A user may be:

* Resident in Society A
* Committee Member in Society B
* Admin in Society C

Membership is society-specific.

---

## 3. Subscription

Subscription answers:

> Is this society allowed to use the platform?

Subscription is attached to the Society.

NOT to individual users.

---

## 4. Authentication

Authentication answers:

> Is the user who they claim to be?

---

## 5. Authorization

Authorization answers:

> What can this authenticated user access?

---

# User Types

## Platform Admin

Managed by your company.

Responsibilities:

* Create societies
* Enable subscriptions
* Suspend societies
* Create primary admin
* Monitor platform

---

## Society Admin

Created by Platform Admin.

Responsibilities:

* Configure society
* Create committee members
* Add residents
* Approve membership requests
* Manage buildings
* Manage units
* Manage visitors
* Manage staff

---

## Committee Member

Permissions assigned by Society Admin.

---

## Resident

Regular member of society.

---

## Security Guard

Limited operational permissions.

---

# Complete Society Onboarding Flow

```
Customer
    │
    ▼
Contacts Company
    │
    ▼
Offline Discussion
    │
    ▼
Subscription Selected
    │
    ▼
Offline Payment
    │
    ▼
Payment Verified
    │
    ▼
Platform Admin Creates Society
    │
    ▼
Primary Admin Account Created
(Status = Pending Activation)
    │
    ▼
Activation Email Sent
    │
    ▼
Admin Activates Account
    │
    ▼
Admin Login
    │
    ▼
Admin Dashboard
    │
    ▼
Configure Society
```

---

# Why No Public Admin Signup?

Public Admin Signup introduces several risks:

* Fake societies
* Spam registrations
* Security attacks
* Unverified customers
* Subscription abuse

Instead:

Only Platform Admin can create Society Admin accounts.

This is the standard enterprise SaaS onboarding model.

---

# Public Website

```
abcsocietymanagement.com

-----------------------------------

Home

Login

Resident Signup

Register Your Society

Forgot Password

-----------------------------------
```

Notice:

There is NO Admin Signup page.

---

# Register Your Society

This replaces Admin Signup.

Purpose:

Collect customer information.

Example Form

```
Organization Name

Primary Contact Name

Email

Mobile Number

City

Expected Number of Flats

Expected Number of Admins

Comments
```

After submission:

Status:

```
Lead Created
```

Platform team contacts customer.

---

# Platform Admin Workflow

After payment verification:

Platform Admin performs:

```
Create Society

↓

Create Subscription

↓

Create Primary Admin

↓

Generate Activation Token

↓

Send Activation Email
```

---

# Admin Account Activation

Email contains:

```
https://abcsocietymanagement.com/activate?token=XYZ123
```

Admin opens link.

Sets:

* Password
* Confirm Password

(Optional)

* MFA

After activation:

```
Status

ACTIVE
```

---

# Admin Login Flow

```
Admin

↓

Login

↓

Authentication

↓

Load Membership

↓

Check Subscription

↓

Redirect

/admin/dashboard
```

Subscription validation happens after authentication.

If subscription expired:

```
Login Successful

↓

Subscription Expired

↓

Read-only Dashboard

OR

Subscription Expired Page
```

NOT during signup.

---

# Society Configuration

After first login:

```
Admin Dashboard

↓

Society Profile

↓

Buildings

↓

Floors

↓

Units

↓

Committee Members

↓

Residents

↓

Security Guards

↓

Amenities

↓

Maintenance Settings

↓

Visitor Rules
```

---

# Resident Onboarding

Residents CAN self-register.

Flow:

```
Resident Signup

↓

Verify Email

↓

Identity Created

↓

Login

↓

Search Society

↓

Request Membership

↓

Admin Approval

↓

Dashboard Enabled
```

---

# Resident Signup

Fields

```
First Name

Last Name

Email

Mobile Number

Password
```

System creates:

Identity only.

NOT membership.

---

# Resident Dashboard Before Approval

Immediately after login:

```
Welcome Mahavir

Membership Status

Pending

Please search your society and submit
a membership request.
```

No society data is visible.

---

# Search Society

Resident searches:

```
ABC Society

ABC Residency

Green Valley

Sky Heights
```

Recommended search filters:

* Society Name
* City
* Society Code

---

# Membership Request

Resident selects society.

Clicks:

```
Request Membership
```

Request generated:

```
Resident

↓

Society Admin
```

---

# Admin Approval Workflow

Admin Dashboard

```
Membership Requests

---------------------------------

Mahavir Rajpurohit

Flat:
A-302

Approve

Reject

---------------------------------
```

---

# After Approval

Membership becomes

```
ACTIVE
```

Resident Dashboard unlocks.

Resident can access:

* Maintenance
* Visitors
* Complaints
* Notices
* Documents

---

# Authentication Flow

Single endpoint.

```
POST /auth/login
```

Input

```
Email

Password
```

Flow

```
Authenticate Identity

↓

Load Memberships

↓

Determine Active Society

↓

Determine Roles

↓

Issue JWT

↓

Redirect
```

---

# Authorization

Examples

```
Resident

↓

Can View

Bills

Complaints

Visitors

Notice Board
```

```
Committee Member

↓

Can Approve

Complaints

Visitors

Bookings
```

```
Society Admin

↓

Full Access
```

---

# Subscription Flow

Subscription belongs to Society.

```
Society

↓

Subscription

↓

Plan

↓

Expiry Date

↓

Max Admin Count

↓

Max Storage

↓

Feature Flags
```

Example

```
Gold Plan

10 Admins

Unlimited Residents

10 GB Storage

Premium Reports
```

---

# Database Model

## Users

```
id

first_name

last_name

email

mobile

password_hash

status

email_verified

created_at
```

---

## Societies

```
id

name

city

status

subscription_id
```

---

## Memberships

```
id

user_id

society_id

role

status

joined_at
```

---

## Subscriptions

```
id

society_id

plan

status

start_date

expiry_date

max_admins

features
```

---

## Activation Tokens

```
id

user_id

token

expires_at

used_at
```

---

# User States

## Society Admin

```
LEAD_CREATED

↓

PAYMENT_PENDING

↓

PAYMENT_VERIFIED

↓

ACCOUNT_CREATED

↓

ACTIVATION_PENDING

↓

ACTIVE

↓

SUSPENDED
```

---

## Resident

```
REGISTERED

↓

EMAIL_VERIFIED

↓

MEMBERSHIP_PENDING

↓

APPROVED

↓

ACTIVE

↓

REMOVED
```

---

# Security Recommendations

* Passwords stored using Argon2 or bcrypt.
* Email verification required.
* Optional MFA for Admin accounts.
* JWT access tokens with refresh tokens.
* Audit logs for admin actions.
* Rate limiting on login endpoints.
* CAPTCHA on public forms.
* One-time activation tokens with expiry.
* All communication over HTTPS.
* Tenant isolation enforced in every database query.

---


# API Endpoints

## Public

```
POST /register-society
POST /auth/login
POST /auth/resident/signup
POST /auth/forgot-password
POST /auth/reset-password
POST /auth/verify-email
POST /auth/activate
```

---

## Resident

```
POST /membership/request

GET /membership/status

GET /dashboard
```

---

## Society Admin

```
POST /societies

PUT /societies/{id}

POST /members

GET /membership/requests

POST /membership/{id}/approve

POST /membership/{id}/reject

POST /committee-members

POST /security-guards
```

---

## Platform Admin

```
POST /platform/societies

POST /platform/subscriptions

POST /platform/admins

POST /platform/send-activation

PUT /platform/subscriptions/{id}

GET /platform/dashboard
```

---

# Future Enhancements

As the platform grows, the following capabilities can be added without changing the overall architecture:

* Online subscription payments
* Automatic subscription renewal
* Identity Provider (SSO)
* Google Login
* Microsoft Login
* WhatsApp OTP
* SMS OTP
* Mobile applications
* Multiple societies per user
* Multi-language support
* Feature flags per subscription plan
* Audit dashboards
* Analytics and reporting

---

# Conclusion

This architecture follows enterprise SaaS principles by clearly separating:

1. **Business Onboarding** (customer acquisition and subscription)
2. **Identity Management** (authentication and account lifecycle)
3. **Membership Management** (society association and roles)
4. **Authorization** (permissions and access control)
5. **Subscription Management** (plan enforcement and feature availability)

The result is a secure, scalable, multi-tenant platform that minimizes operational effort after onboarding while allowing society administrators to independently manage and configure their societies.



1. User Login Dashboard (Firstime user)
    ┌─────────────────────────────────────────────────────────┐                                                                                                        
    │ 1. JOIN YOUR SOCIETY                                    │                                                                                                        
    │ Search: [ Shashikant APT                       ▼ ]      │                                                                                                        
    ├─────────────────────────────────────────────────────────┤                                                                                                        
    │ 2. SELECT YOUR UNIT LOCATION                            │                                                                                                        
    │ Building / Wing:  [ a_wing                     ▼ ]      │                                                                                                        
    │ Floor:            [ Floor 1                    ▼ ]      │                                                                                                        
    │ Flat Number:      [ Flat 101                   ▼ ]      │                                                                                                        
    │                                                         │                                                                                                        
    │ Ownership Type:   (•) Owner   ( ) Tenant                │                                                                                                        
    ├─────────────────────────────────────────────────────────┤                                                                                                        
    │                   [ SUBMIT REQUEST ]                    │                                                                                                        
    └─────────────────────────────────────────────────────────┘    

      ##### ⚙️ How Frontend Code Executes This:
  
  1. When user selects a_wing, Frontend calls GET /buildings/{id}/floors.
  2. When user selects Floor 1, Frontend calls GET /floors/{id}/units.   
  3. When user clicks "Submit Request", Frontend grabs the UUID of Flat 101 behind the scenes and sends:
    {
      "society_id": "b608d953-5e22-4863-b81b-7cd9c7feff5b",
      "unit_id": "fedfbe4a-f477-402f-8716-c0b6f89d7794",   
      "role": "resident"
    }

  #### 💻 B. The Society Admin's Web Dashboard UI
  
    ┌────────────────────────────────────────────────────────────────────────┐
    │ PENDING RESIDENT REQUESTS (1)                                          │
    ├────────────────────────────────────────────────────────────────────────┤
    │ Resident Name : Darklight Day                                          │
    │ Email         : darklightday81@gmail.com                               │
    │ Requested Unit: Wing A -> Floor 1 -> Flat 101 (Owner)                  │
    │ Status        : PENDING APPROVAL                                       │
    │                                                                        │
    │                 [ APPROVE & ASSIGN ]    [ REJECT ]                     │
    └────────────────────────────────────────────────────────────────────────┘
    
  ##### ⚙️ How Frontend Code Executes This:
  
  1. The Admin clicks "APPROVE & ASSIGN".
  2. Frontend calls POST /societies/{society_id}/membership/{membership_id}/approve.
  3. The backend updates membership to approved, assigns the user to Flat 101, and sends a Resend Email Notification to the resident! 📧 



  ##### if User has to be associated with a particuler flat(unit id) the follow the below flow


  ### 1️⃣ Who Performs This Flow: User or Admin?                                                                                                                        
                                                                                                                                                                       
  In enterprise society platforms, BOTH roles participate in a smooth 2-step process:                                                                                  
                                                                                                                                                                       
  1. The Resident (User): Selects their flat during signup (Self-Service).                                                                                             
  2. The Society Admin: Verifies & Approves the selection (Access Control & Security).                                                                                 
                                                                                                                                                                       
  │ Why this design?                                                                                                                                                   
  │ If the Admin had to manually type and assign flats for 500 residents, it would be overwhelming. Having residents pick their flat from a dropdown list reduces the  
  │ Admin's job to a single click of an "Approve" button!                                                                                                              
  ──────                                                                                                                                                               
  ### 2️⃣ How It Works on the Frontend (Step-by-Step UI Journey)                                                                                                        
                                                                                                                                                                       
  #### 📱 A. The Resident's Mobile / Web App UI                                                                                                                        
                                                                                                                                                                       
    ┌─────────────────────────────────────────────────────────┐                                                                                                        
    │ 1. JOIN YOUR SOCIETY                                    │                                                                                                        
    │ Search: [ Shashikant APT                       ▼ ]      │                                                                                                        
    ├─────────────────────────────────────────────────────────┤                                                                                                        
    │ 2. SELECT YOUR UNIT LOCATION                            │                                                                                                        
    │ Building / Wing:  [ a_wing                     ▼ ]      │                                                                                                        
    │ Floor:            [ Floor 1                    ▼ ]      │                                                                                                        
    │ Flat Number:      [ Flat 101                   ▼ ]      │                                                                                                        
    │                                                         │                                                                                                        
    │ Ownership Type:   (•) Owner   ( ) Tenant                │                                                                                                        
    ├─────────────────────────────────────────────────────────┤                                                                                                        
    │                   [ SUBMIT REQUEST ]                    │                                                                                                        
    └─────────────────────────────────────────────────────────┘                                                                                                        
                                                                                                                                                                       
  ##### ⚙️ How Frontend Code Executes This:                                                                                                                            
                                                                                                                                                                       
  1. When user selects a_wing, Frontend calls GET /buildings/{id}/floors.                                                                                              
  2. When user selects Floor 1, Frontend calls GET /floors/{id}/units.                                                                                                 
  3. When user clicks "Submit Request", Frontend grabs the UUID of Flat 101 behind the scenes and sends:                                                               
    {                                                                                                                                                                  
      "society_id": "b608d953-5e22-4863-b81b-7cd9c7feff5b",                                                                                                            
      "unit_id": "fedfbe4a-f477-402f-8716-c0b6f89d7794",                                                                                                               
      "role": "resident"                                                                                                                                               
    }                                                                                                                                                                  
                                                                                                                                                                       
  ──────                                                                                                                                                               
  #### 💻 B. The Society Admin's Web Dashboard UI                                                                                                                      
                                                                                                                                                                       
    ┌────────────────────────────────────────────────────────────────────────┐                                                                                         
    │ PENDING RESIDENT REQUESTS (1)                                          │                                                                                         
    ├────────────────────────────────────────────────────────────────────────┤                                                                                         
    │ Resident Name : Darklight Day                                          │                                                                                         
    │ Email         : darklightday81@gmail.com                               │                                                                                         
    │ Requested Unit: Wing A -> Floor 1 -> Flat 101 (Owner)                  │                                                                                         
    │ Status        : PENDING APPROVAL                                       │                                                                                         
    │                                                                        │                                                                                         
    │                 [ APPROVE & ASSIGN ]    [ REJECT ]                     │                                                                                         
    └────────────────────────────────────────────────────────────────────────┘                                                                                         
                                                                                                                                                                       
  ##### ⚙️ How Frontend Code Executes This:                                                                                                                            
                                                                                                                                                                       
  1. The Admin clicks "APPROVE & ASSIGN".                                                                                                                              
  2. Frontend calls POST /societies/{society_id}/membership/{membership_id}/approve.                                                                                   
  3. The backend updates membership to approved, assigns the user to Flat 101, and sends a Resend Email Notification to the resident! 📧                               
  ──────                                                                                                                                                               
  ### 🎯 Summary                                                                                                                                                       
                                                                                                                                                                       
  • Resident: Picks their flat from clean cascading dropdowns (Wing → Floor → Flat).                                                                                   
  • Admin: Clicks Approve to grant official access.                                                                                                                    

────────────────────────────────────────────────────────────
> okay and if Admin only has to perform the whole flow then how it will work in frontend from the Admin side

▸ Thought for 6s, 687 tokens
  Clarifying Admin UI Flow
  If the Admin performs 100% of the unit assignment flow, here is how the Admin Portal UI works step-by-step:                                                          
  ──────                                                                                                                                                               
  ### 💻 Admin Portal UI Layout & Experience                                                                                                                           
                                                                                                                                                                       
  In the Admin Dashboard, there is a dedicated page called "Resident Directory & Unit Allocations".                                                                    
                                                                                                                                                                       
  #### Screen 1: Unassigned Residents Table                                                                                                                            
                                                                                                                                                                       
  The Admin sees a table of all approved or pending residents who don't have a flat assigned yet:                                                                      
                                                                                                                                                                       
    ┌──────────────────────────────────────────────────────────────────────────────────────────┐                                                                       
    │ UNASSIGNED RESIDENTS (Waiting for Flat Allocation)                                        │                                                                      
    ├──────────────────┬──────────────────────────┬─────────────────┬──────────────────────────┤                                                                       
    │ RESIDENT NAME    │ EMAIL                    │ JOIN DATE       │ ACTION                   │                                                                       
    ├──────────────────┼──────────────────────────┼─────────────────┼──────────────────────────┤                                                                       
    │ Darklight Day    │ darklightday81@gmail.com │ 30 July 2026    │ [ 🏠 Assign to Unit ]    │                                                                       
    │ Rohan Sharma     │ rohan@example.com        │ 30 July 2026    │ [ 🏠 Assign to Unit ]    │                                                                       
    └──────────────────┴──────────────────────────┴─────────────────┴──────────────────────────┘                                                                       
    ──────                                                                                                                                                             
  #### Screen 2: Assign Unit Modal (Opens when Admin clicks "[ 🏠 Assign to Unit ]")                                                                                   
                                                                                                                                                                       
  A clean popup modal appears over the dashboard:                                                                                                                      
                                                                                                                                                                       
    ┌──────────────────────────────────────────────────────────────────────────────────────────┐                                                                       
    │ 🏠 ASSIGN RESIDENT TO FLAT UNIT                                                          │                                                                       
    ├──────────────────────────────────────────────────────────────────────────────────────────┤                                                                       
    │ Resident: Darklight Day (darklightday81@gmail.com)                                       │                                                                       
    │                                                                                          │                                                                       
    │ 1. Select Building/Wing:  [ a_wing                                              ▼ ]      │
    │ 2. Select Floor:          [ Floor 1 (Floors 1-3)                                ▼ ]      │
    │ 3. Select Flat / Unit:    [ Flat 101 (Vacant)                                   ▼ ]      │
    │                                                                                          │
    │ Occupancy Type:           (•) Owner   ( ) Tenant                                     │
    │ Set as Primary Contact:   [x] Yes, Primary Resident                              │
    │                                                                                          │
    │                           [ CANCEL ]    [ 🚀 CONFIRM & SAVE ALLOCATION ]                 │
    └──────────────────────────────────────────────────────────────────────────────────────────┘
    ──────
  ### ⚙️ What Frontend Code Executes Behind the Scenes
  
  When the Admin clicks "[ 🚀 CONFIRM & SAVE ALLOCATION ]", the frontend executes 2 API calls in 1 second:
  
  #### Call 1: Binds User to the Flat Unit
  
    POST /api/v1/societies/{society_id}/units/{unit_id}/residents
    Content-Type: application/json
  
    {
      "user_id": "8b83f901-89dd-40d7-9d82-0586949e03e2",
      "ownership_type": "owner",
      "is_primary": true
    }
  
  #### Call 2: Approves Membership & Triggers Resend Email
  
    POST /api/v1/societies/{society_id}/membership/{membership_id}/approve
    ──────
  ### 🎉 Result on the Screen
  
  1. The modal closes automatically.
  2. A green success toast notification appears:
  "Darklight Day successfully assigned to Wing A - Flat 101! Notification email sent."
  3. The resident moves from the "Unassigned List" to the "Flat 101 Occupants List".
