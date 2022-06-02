@main
Feature: Check Settings Page

  Scenario: Add Channel Filter
    When Open settings page

    Then We see settings page

    When Click Add new Escalation chain

    Then We see new Escalation chain popup

    When We input Filtering Term

    When Click Create

