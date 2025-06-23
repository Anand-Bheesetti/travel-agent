# AI Travel Agent & Expense Planner

This project is an AI-powered travel agent that helps users plan trips to any city worldwide. It provides real-time information, generates a complete itinerary, and calculates expenses, offering an interactive and iterative planning experience.

## Core Architecture

The application is built with a modular and scalable architecture, separating the user interface from the core logic.

- **`app.py`**: The main entry point for the Streamlit user interface. It handles user interactions, chat history, and calls the backend workflow.
- **`workflow.py`**: Contains the LangGraph implementation. It defines the agent's state, the graph of nodes, and the conditional logic that drives the conversation.
- **`services.py`**: A collection of Python classes, each responsible for a specific task (e.g., fetching weather, finding attractions, calculating costs). These are the "tools" our agent uses.
- **`models.py`**: Defines the Pydantic data models (`TripPlan`, `QueryAnalysisResult`) that ensure structured and validated data flows through the system.
- **`requirements.txt`**: Lists all project dependencies.
- **`.env`**: Stores sensitive information like API keys. (Note: create this file from `.env.example`).

## Data Flow & Conversational Logic

The agent operates in three distinct phases to provide a natural and efficient user experience. The flow is managed by the `TravelWorkflow` in `workflow.py`.

### Phase 1: Information Collection

1.  **User Input**: The user starts with an initial query (e.g., "I want to go to Paris").
2.  **Query Analyzer**: The `QueryAnalyzer` node uses an LLM to parse the query and populate the `TripPlan` model. It identifies any essential missing information (`destination`, `days`, `budget`, etc.).
3.  **Interactive Collector**: If information is missing, the workflow enters a loop, asking the user targeted questions one by one until all required fields in the `TripPlan` state are filled.

### Phase 2: Complete Plan Generation

1.  **Trip Planner**: Once all necessary information is collected, the workflow triggers a sequence of service calls:
    - `WeatherService` fetches the forecast.
    - `AttractionFinder` gets a list of relevant activities.
    - `HotelCalculator` estimates accommodation costs.
    - `CurrencyConverter` converts costs to the user's native currency.
2.  **Itinerary Builder**: The `ItineraryBuilder` takes all the gathered data and constructs a day-by-day itinerary.
3.  **Summary Generator**: A final summary of the entire trip, including total estimated cost, is generated and presented to the user.

### Phase 3: Iterative Refinement

1.  **User Feedback**: After seeing the complete plan, the user can provide feedback or request changes (e.g., "Can you find a cheaper hotel?", "I'd like to add another day").
2.  **Plan Router**: The workflow's entry router detects that a complete plan already exists in the agent's state. It routes the new input to a `PlanModifier` node instead of starting from scratch.
3.  **Plan Modifier**: This node analyzes the user's modification request, updates the `trip_plan` state accordingly, and re-runs only the necessary planning steps (e.g., only re-running the `HotelCalculator` if the budget changes).
4.  The updated plan is presented, and the user can continue to refine it until they are satisfied.

This cyclical, stateful approach allows for a flexible and powerful conversation, making the planning process collaborative and user-friendly.
