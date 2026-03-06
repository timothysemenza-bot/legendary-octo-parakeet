You are continuing development of the Boss Key Pursuit OS repository.

Before making any changes, perform the following due-diligence steps.

STEP 1 — CURRENT STATE REVIEW

Analyze the entire repository and summarize:

1. What functionality is currently implemented
2. What modules exist and their current status
3. What files were most recently added or modified
4. The current database schema and tables
5. Any known technical debt or fragile areas
6. Any failing or missing tests
7. The current phase of the development roadmap

Keep this summary concise and factual.

STEP 2 — ARCHITECTURE VALIDATION

Confirm that the system architecture remains consistent with the original design:

Modules should remain separated as:

opportunity_intake  
rfp_parser  
compliance_matrix  
capture_plan  
proposal_outline  
review_manager  
submission_checklist  

The layers must remain:

Web layer  
Module layer  
Core utilities  
Knowledge layer  

If you detect architectural drift, explain it before proceeding.

STEP 3 — DEFINE THE NEXT TASK

Based on the roadmap and current system state, identify the next logical implementation step.

Describe:

• the exact module or feature to implement  
• what files will be created or modified  
• whether the database schema must change  
• whether any existing contracts must change  

Do not begin coding until this plan is stated.

STEP 4 — IMPLEMENTATION RULES

When implementing the task:

• Modify only files required for the task  
• Preserve existing APIs and data contracts unless absolutely necessary  
• Maintain modular separation between modules  
• Avoid refactoring unrelated components  
• Add documentation where useful  
• Maintain clear naming and code readability  

STEP 5 — TESTING

After implementation:

1. Add unit tests where appropriate
2. Add integration tests if workflows are affected
3. Run the full test suite
4. Fix any failing tests

Do not move forward until tests pass.

STEP 6 — POST-IMPLEMENTATION SUMMARY

After completing the task, report:

1. Files added
2. Files modified
3. Database changes (if any)
4. New capabilities added
5. Any technical debt introduced
6. Any risks or limitations

STEP 7 — DEFINE THE NEXT STEP

Finally state the next recommended implementation step for the system.

Do not begin implementing that next step yet.

Stop after reporting.
