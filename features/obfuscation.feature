Feature: Code Obfuscation Security Requirements
  As a security engineer
  I want to ensure that code obfuscation meets baseline security invariants
  So that sensitive logic and data cannot be easily recovered

  Scenario: Obfuscated string literals are not trivially grep-able
    Given a Python source file containing the secret string "SUPER_SECRET_DATABASE_PASSWORD_2026"
    When I obfuscate the source using the "polymorphic" string strategy
    Then the obfuscated output must not contain the literal string "SUPER_SECRET_DATABASE_PASSWORD_2026"
    And executing the obfuscated code should still produce "SUPER_SECRET_DATABASE_PASSWORD_2026"

  Scenario: Function names are properly mangled
    Given a Python source file containing a function named "calculate_enterprise_revenue"
    When I obfuscate the source with variable renaming enabled
    Then the obfuscated output must not contain the exact identifier "calculate_enterprise_revenue"
    And executing the obfuscated code should execute the original function logic

  Scenario: Control Flow Flattening removes clear execution paths
    Given a Python source file with a sequential function "process_data"
    When I obfuscate the source with control flow flattening enabled
    Then the obfuscated output must contain a while loop dispatch mechanism
    And the obfuscated output must not contain the original sequential statement order
    And executing the obfuscated code should yield the same result as the original