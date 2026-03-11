# Cypress Testing for Tailwind CSS

## Windows Troubleshooting

If you encounter issues with Cypress on Windows (like the "bad option: --smoke-test" error), you can try the following solutions:

1. **Use WSL (Windows Subsystem for Linux)**: Run Cypress in a Linux environment through WSL.

2. **Run in headless mode**: Instead of using `cypress open`, use `cypress run` to run tests without the GUI.

3. **Downgrade Cypress**: If the issue persists, try installing an older version of Cypress:
   ```bash
   npm install cypress@14.0.0 --save-dev
   ```

4. **Check Windows dependencies**: Ensure you have all required Windows dependencies installed as mentioned in the [Cypress documentation](https://on.cypress.io/required-dependencies).

## Running Tests

To run the Tailwind CSS tests:

1. Start the development server:
   ```bash
   npm run dev
   ```

2. In another terminal, run the tests:
   ```bash
   npm run cypress:run
   ```

3. To run tests automatically with the dev server:
   ```bash
   npm run test:e2e
   ```

## Test Results

Test results will be displayed in the terminal and logged to the browser console for debugging purposes. You can view these logs in the browser's developer tools console when running the tests.