# How to Create a GitHub Copilot Custom Agent for Test Setup

This guide explains how to use the `copilot-test-agent-prompt.md` file to create a GitHub Copilot Custom Agent that ensures tests are properly set up and executed in the Printernizer project.

## What is a GitHub Copilot Custom Agent?

GitHub Copilot Custom Agents are specialized AI assistants that you can create in GitHub Copilot Workspace or GitHub Copilot Chat. They have domain-specific knowledge and can help with specific tasks like test setup, debugging, or code reviews.

## Step-by-Step Setup

### Option 1: Using GitHub Copilot Workspace

1. **Open GitHub Copilot Workspace**
   - Navigate to your repository on GitHub
   - Click on "Copilot" in the top navigation
   - Select "Workspace"

2. **Create a New Custom Agent**
   - In Copilot Workspace, look for "Custom Agents" or "Agent Builder"
   - Click "Create New Agent"

3. **Configure the Agent**
   - **Agent Name**: `Test Setup and Execution Expert`
   - **Description**: `Specialized agent for Printernizer test infrastructure setup, execution, and troubleshooting`
   - **Agent Prompt**: Copy and paste the entire content of `.github/copilot-test-agent-prompt.md`

4. **Activate the Agent**
   - Save the agent configuration
   - The agent will now be available in your Copilot Workspace

### Option 2: Using GitHub Copilot Chat (VS Code Extension)

1. **Open VS Code with GitHub Copilot**
   - Ensure you have GitHub Copilot extension installed
   - Open the Printernizer repository in VS Code

2. **Create Agent Instructions**
   - Create a file in your project: `.github/copilot/test-agent.md`
   - Copy the content from `copilot-test-agent-prompt.md` into this file
   - Some versions of Copilot automatically detect agent instruction files

3. **Use the Agent**
   - Open GitHub Copilot Chat (Ctrl+I or Cmd+I)
   - Reference the agent: `@test-agent` or load the instructions manually
   - Ask questions like: "Set up the test environment" or "Run integration tests"

### Option 3: Direct Prompt Usage

If custom agents are not available in your GitHub Copilot version, you can use the prompt directly:

1. **Copy the Prompt Content**
   - Open `.github/copilot-test-agent-prompt.md`
   - Copy the entire content

2. **Start a Copilot Chat Session**
   - Open GitHub Copilot Chat
   - Paste the prompt content as context
   - Then ask your specific question

3. **Example Interaction**
   ```
   [Paste the agent prompt content]
   
   Now, help me set up the test environment for the first time.
   ```

## Using the Test Agent

Once your custom agent is set up, you can ask it questions like:

### Test Environment Setup
- "Set up the test environment from scratch"
- "Verify all test dependencies are installed"
- "Check if pytest configuration is correct"

### Running Tests
- "Run all unit tests"
- "Execute integration tests with coverage"
- "Run German business logic compliance tests"
- "Show me the coverage report for printer_service.py"

### Troubleshooting
- "Why are my tests failing in CI but passing locally?"
- "How do I fix 'Event loop already running' errors?"
- "Tests are running slowly, how can I speed them up?"

### Writing Tests
- "Help me write tests for the new file_service feature"
- "Show me how to test async functions properly"
- "Create parametrized tests for IP address validation"

### Coverage Analysis
- "Which modules have low test coverage?"
- "How can I increase coverage for German compliance code to 100%?"
- "Generate a coverage report and identify gaps"

## Expected Agent Behavior

When you interact with the test agent, it should:

1. **Understand Context**: It knows about pytest, async tests, German business logic requirements
2. **Provide Commands**: Give exact commands to run tests, check coverage, etc.
3. **Troubleshoot Issues**: Diagnose test failures and suggest fixes
4. **Follow Best Practices**: Recommend AAA pattern, proper fixtures, test isolation
5. **Focus on Quality**: Ensure high coverage, especially for critical German compliance code

## Example Interactions

### Example 1: Setup Help
```
User: I'm setting up tests for the first time. What do I need?

Agent: Let me help you set up the test environment. Here's the checklist:

1. Verify Python version:
   python --version  # Should be 3.12+

2. Install test dependencies:
   pip install -r requirements-test.txt

3. Verify pytest is installed:
   python -m pytest --version

4. Check test discovery:
   pytest --collect-only

5. Run a simple test to verify setup:
   pytest tests/test_infrastructure.py -v

Let me know if any step fails!
```

### Example 2: Running Tests
```
User: Run all integration tests with coverage

Agent: Here's how to run integration tests with coverage:

pytest -m integration --cov=src --cov-report=html --cov-report=term-missing tests/

This will:
- Run only tests marked with @pytest.mark.integration
- Generate coverage for the src/ directory
- Create an HTML report in htmlcov/
- Show missing lines in the terminal

After running, view the HTML report:
open htmlcov/index.html
```

### Example 3: Troubleshooting
```
User: My async tests are failing with "Event loop already running"

Agent: This is a common async test issue. Here's how to fix it:

1. Check your pytest.ini has:
   asyncio_mode = auto

2. Ensure your test uses the decorator:
   @pytest.mark.asyncio
   async def test_my_async_function():
       result = await my_function()
       assert result is not None

3. If you have conflicting fixtures, ensure they don't create their own event loops.

4. For test isolation, avoid sharing async resources between tests.

Would you like me to check a specific test file?
```

## Maintenance

### Updating the Agent Prompt
When the test infrastructure changes:
1. Update `.github/copilot-test-agent-prompt.md`
2. Recreate or update the custom agent with the new prompt
3. Test the agent with sample questions to ensure accuracy

### Keeping It Current
Review and update the prompt when:
- Test frameworks are upgraded (e.g., pytest version bump)
- New test categories or markers are added
- German compliance requirements change
- New testing best practices are adopted

## Limitations

- The agent's knowledge is limited to what's in the prompt
- It cannot directly execute commands (you need to run them)
- It may not be aware of very recent changes unless the prompt is updated
- Some GitHub Copilot versions may not support custom agents yet

## Alternative: Claude Agent

Note: This project also has `.claude/agents/testing-agent.md` for Claude-based development. The GitHub Copilot agent is specifically optimized for GitHub's Copilot interface and workflow.

## Support

If you encounter issues with the agent:
1. Check that you copied the complete prompt
2. Verify your GitHub Copilot version supports custom agents
3. Try using the prompt directly in a chat session
4. Consult GitHub Copilot documentation for custom agent features

---

**Questions?** Open an issue in the repository or refer to GitHub Copilot's official documentation for custom agent features.
