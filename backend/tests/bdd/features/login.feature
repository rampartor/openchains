Feature: User login
  Scenario: Valid login
    Given I have a user "alice" with password "secret"
    When I post to "/login" with those credentials
    Then I should receive a 200 status code
    And the response should include "Hello, alice!"
