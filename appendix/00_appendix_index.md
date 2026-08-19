# StringSense Appendix Material Index

This folder contains supporting materials for the FYP report. FYP1 claim
boundaries remain explicit, while API, schema, and testing summaries describe
the current implementation and label later FYP2 evidence separately. It should
not be treated as only system screenshots.

| Appendix | Material | Purpose |
| --- | --- | --- |
| Appendix A | System screenshots (`*.png`) | Shows the implemented player and admin user interfaces. |
| Appendix B | `B_api_endpoint_summary.md` | Documents the backend API surfaces used by the mobile app. |
| Appendix C | `C_database_schema_summary.md` | Summarizes the major database tables and ownership boundaries. |
| Appendix D | `D_recommendation_algorithm.md` | Explains the recommendation scoring method, formula, and evidence sources. |
| Appendix E | `E_key_code_extracts.md` | Identifies representative source-code excerpts to include in the report. |
| Appendix F | `F_testing_evidence.md` | Summarizes backend test cases that verify core FYP1 behavior. |
| Appendix G | `G_nlp_artifacts.md` | Lists the NLP notebooks and generated matrix files used by the recommender. |

Suggested usage in the report:

1. Place screenshots after the implementation chapter or as Appendix A.
2. Place API/database/algorithm details after the technical design chapter.
3. Place code extracts and test evidence after the testing/evaluation chapter.
4. State that payment, wallet, chat, notifications, racket passport, service
   queue, and check-in are now implemented and tested, but are not claimed as
   completed FYP1 deliverables.
