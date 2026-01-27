describe('Tailwind CSS Test', () => {
  beforeEach(() => {
    // Visit the application
    cy.visit('/')
  })

  it('should display the application with Tailwind styles', () => {
    // Check if the app container exists
    cy.get('#root').should('exist')
    
    // Check if the main App component has the expected structure
    cy.get('body').should('exist')
    
    // Check if Tailwind classes are applied correctly
    // Verify the glass panel styling
    cy.get('.input-field').should('have.css', 'border-radius')
      .and('include', '0.75rem') // rounded-xl from input-field utility
    
    // Check the input field styling
    cy.get('.input-field').should('have.css', 'border-radius')
      .and('include', '0.75rem') // This is 12px which is rounded-xl
    
    // Check the button styling
    cy.get('.btn-primary').should('have.css', 'background')
      .and('include', 'gradient')
    
    // Log test results to the browser console
    cy.log('Tailwind CSS test completed successfully')
    cy.logToConsole('Cypress test result: Tailwind CSS is working correctly')
  })

  it('should verify responsive design classes', () => {
    // Test mobile view
    cy.viewport('iphone-6')
    cy.get('body').should('be.visible')
    
    // Check if the grid changes to single column on mobile
    cy.get('.grid-cols-1').should('exist')
    
    // Test desktop view
    cy.viewport('macbook-15')
    cy.get('body').should('be.visible')
    
    // Check lg:grid-cols-12 on input grid for desktop
    cy.get('.lg\\:grid-cols-12').should('exist')
    
    // Log test results to the browser console
    cy.logToConsole('Cypress test result: Responsive design classes are working')
  })
  
  it('should verify custom utility classes', () => {
    // Check if the glass panel class is applied
    cy.get('nav').should('have.class', 'glass-panel')
    
    // Check if the text glow effect is applied
    cy.get('h2').find('span').should('have.class', 'text-glow')
    
    // Check if the border glow effect is applied
    cy.get('section').eq(1).should('have.class', 'border-glow')
    
    // Log test results to the browser console
    cy.logToConsole('Cypress test result: Custom utility classes are working')
  })
})