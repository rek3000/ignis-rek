Here are instructions for creating an Ignis dexscreener token price tracker module:

1. Project Structure
- Create module in `modules/price_tracker` directory
- Implement primary module files:
  - `__init__.py`
  - `main.py`
  - Potentially `utils.py` for additional helpers

2. Core Module Components
- Import required Ignis libraries
- Create class-based structure similar to notification popup
- Implement core classes for price tracking functionality

3. Key Implementation Requirements
- Use `IgnisApp.get_default()` for app integration
- Leverage Ignis widget classes for UI components
- Implement notification system for price changes
- Handle dynamic data retrieval and display

4. Recommended Module Flow
- Create price tracking logic
- Develop widget for displaying prices
- Integrate notification mechanism
- Implement periodic price checking
- Allow user configuration for tracked items

5. Technical Considerations
- Use `Widget` classes for UI elements
- Implement reveal/animation effects similar to notification popup
- Handle multiple price tracking instances
- Create configurable update intervals
- Manage error scenarios for price retrieval

6. Suggested Module Architecture
- Base class for price tracking
- Specific implementation classes
- Configuration management
- Data retrieval service
- Notification handling
- Error management

7. Development Best Practices
- Follow existing Ignis module patterns
- Maintain consistent coding style
- Implement robust error handling
- Create flexible, configurable design
- Use type hints
- Write clear documentation