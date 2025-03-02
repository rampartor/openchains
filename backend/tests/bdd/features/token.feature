Feature: User authentication
  Scenario: Valid login
    Given I have a user "alice" with password "secret"
    When I post to "/token" with those credentials
    Then I should receive a 200 status code
    And the response should include an access token
