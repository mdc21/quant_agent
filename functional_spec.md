# Functional Specification: YourBestPath Fiduciary Platform

## 1. Overview
The **YourBestPath** platform has been transformed from a raw quantitative engine into a secure, user-centric fiduciary wealth management application. The platform guides users through an intuitive, structured investment journey, prioritizing data security, personalized goal setting, and actionable financial advice.

---

## 2. Screen Organization & Layout Design
The platform's user interface is designed to reduce cognitive load and guide the user logically through complex financial decisions.

### 2.1 Authentication Screen
- **Layout**: 50/50 Split-Screen.
- **Left Panel (Brand)**: Deep navy gradient background featuring glowing concentric rings (Green, Blue, Gold) symbolizing the three pillars of wealth, anchored by the serif "YourBestPath" logo.
- **Right Panel (Action)**: Clean, pure white background featuring a centered, elevated card with subtle drop shadows.
- **Information Hierarchy**: The card contains simple tabs for "Sign In" and "Create Account", vertically stacked input fields, a prominent dark-navy action button, and a bottom security badge assuring 256-bit AES encryption.

### 2.2 Fiduciary Dashboard Hub (Home)
- **Layout**: Full-width container with a persistent sidebar (once logged in).
- **Header**: Personalized welcome message ("Welcome back, [Name]").
- **Information Hierarchy**:
  - **Top Row**: High-level summary metrics (if goals are already defined).
  - **Action Cards**: Three distinct, horizontally aligned action cards acting as the primary navigation routing nodes:
    1. Define Goals (Wizard)
    2. Review Existing Goals
    3. Quick Advice (Lumpsum/SIP)

### 2.3 The Goals Wizard Screens
- **Layout**: Centered, constrained-width container (max 800px) to maintain focus, with a persistent progress indicator at the top.
- **Information Hierarchy per Step**:
  - **Framework View**: Three distinct horizontal bands explaining Survival, Safety, and Growth.
  - **Selection Grid**: A responsive grid of interactive, selectable cards with icons representing specific life goals (e.g., Retirement, Education).
  - **Data Input Forms**: Clean, vertically stacked numeric inputs and sliders that dynamically appear only for the specific goals selected in the previous step.

---

## 3. User Journey Flows & Scenarios

### Scenario A: New User Comprehensive Onboarding
**Profile**: A new user seeking a complete financial plan.
1. **Screen 1 (Auth)**: Lands on the split-screen auth page. Selects "Create Account", inputs details, and clicks register. Immediately signs in.
2. **Screen 2 (Hub)**: Lands on the Fiduciary Dashboard. With no prior data, the user selects "Define Goals".
3. **Screen 3 (Wizard - Intro)**: Reviews the 3-pillar framework. Clicks Next.
4. **Screen 4 (Wizard - Selection)**: Selects "Emergency Fund" (Safety) and "Retirement" (Growth) from the visual grid. Clicks Next.
5. **Screen 5 (Wizard - Details)**: The screen dynamically renders input fields exclusively for Emergency Fund (monthly expenses, target months) and Retirement (target amount, years to retire). User inputs numbers. Clicks Next.
6. **Screen 6 (Wizard - Risk)**: User selects "Moderate" from the risk profiling options.
7. **Screen 7 (Wizard - Summary)**: User reviews the generated summary of their inputs. Clicks "Finalize Plan". The system saves to ArcticDB.
8. **Screen 8 (Main Dashboard)**: The system routes the user back to the Main Dashboard, which now displays their generated portfolio distribution and goal progress.

### Scenario B: Returning User Reviewing Goals
**Profile**: An existing user checking their progress.
1. **Screen 1 (Auth)**: Signs in via the split-screen auth page.
2. **Screen 2 (Hub)**: Lands on the Fiduciary Dashboard. Their existing risk profile and goal summary are visible. The user selects "Review Existing Goals".
3. **Screen 3 (Portfolio Dashboard)**: User views a detailed breakdown of their asset allocation (Equities vs. Fixed Income) and progress bars indicating how close they are to funding their Survival and Growth goals.
4. **Screen 4 (Update)**: User clicks "Update Goals" to re-enter the Wizard with their previous data pre-populated, allowing them to adjust target amounts or timelines.

### Scenario C: Quick Advice Seeker
**Profile**: A user with a sudden cash influx who wants immediate deployment advice.
1. **Screen 1 (Auth)**: Signs in.
2. **Screen 2 (Hub)**: Selects the "Quick Advice" action card, bypassing the full goal wizard.
3. **Screen 3 (Quick Advice Form)**: 
   - User selects "Lump-sum Investment".
   - Inputs capital amount (e.g., $50,000).
   - Selects Investment Horizon (e.g., "Long-term (7+ years)").
   - Selects Risk Profile ("Growth").
   - Clicks "Generate Advice".
4. **Screen 4 (Recommendation)**: The screen immediately reveals a dynamically calculated pie chart and asset allocation table recommending the exact percentage split across Equities, Mutual Funds, and Fixed Income based solely on those rapid inputs.

---

## 4. Telemetry & Observability
- **Activity Logging**: The entire user journey is instrumented with backend logging. Every step progression in the wizard, route selection, and authentication attempt is traced. This ensures the system can provide high-quality support and maintain a verifiable audit trail of fiduciary advice.
