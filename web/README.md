# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Cypress Testing

This project includes Cypress for end-to-end testing of the Tailwind CSS implementation.

### Running Tests

1. Start the development server:
   ```bash
   npm run dev
   ```

2. In another terminal, run the tests:
   ```bash
   npm run cypress:open
   ```

   Or run in headless mode:
   ```bash
   npm run cypress:run
   ```

3. To run tests automatically with the dev server:
   ```bash
   npm run test:e2e
   ```

### Test Results

Test results will be displayed in the Cypress Test Runner and logged to the browser console for debugging purposes.
