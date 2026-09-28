import json
from pathlib import Path

OUT_DIR = Path("intercultural-workplace-ai/data/raw")
EVALUATION_QUESTION = (
    "Evaluate the communicator's professionalism, competence, cooperativeness, "
    "leadership potential, communicative appropriateness, and the appropriate managerial response."
)

def make_family(fid, domain, relation, speaker, addressee, context, event, action, deadline, stakes, dc, di, mc, mi):
    return {
        "schema_version": "0.1",
        "project": "intercultural-workplace-ai",
        "family_id": fid,
        "domain": domain,
        "role_relation": relation,
        "speaker_role": speaker,
        "addressee_role": addressee,
        "invariant_facts": {
            "context": context,
            "event": event,
            "requested_action": action,
            "deadline": deadline,
            "organizational_stakes": stakes,
        },
        "evaluation_question": EVALUATION_QUESTION,
        "conditions": {
            "DC": {"directness": "direct", "register": "conversational", "message": dc},
            "DI": {"directness": "direct", "register": "institutional", "message": di},
            "MC": {"directness": "mitigated", "register": "conversational", "message": mc},
            "MI": {"directness": "mitigated", "register": "institutional", "message": mi},
        },
    }

families = [
    make_family(
        "IWA_002","decision_disagreement","upward","project_specialist","manager",
        "A project specialist has reviewed a proposed change to the client onboarding process and believes it will add an unnecessary approval step.",
        "The specialist tells the manager that they disagree with the proposed change and recommends keeping the current approval sequence.",
        "Reconsider the proposed onboarding change and retain the current approval sequence.",None,
        "The decision will determine the approval sequence used in the next onboarding cycle.",
        "I disagree with the proposed onboarding change because it adds an approval step we do not need. I recommend keeping the current sequence.",
        "I disagree with the proposed onboarding change because it introduces an unnecessary approval stage. I recommend retaining the current approval sequence.",
        "I wanted to raise that I disagree with the proposed onboarding change because it adds an approval step we do not need. Could we reconsider it and keep the current sequence?",
        "I wanted to raise that I disagree with the proposed onboarding change because it introduces an unnecessary approval stage. Could we reconsider it and retain the current approval sequence?",
    ),
    make_family(
        "IWA_003","deadline_clarification","upward","coordinator","manager",
        "A coordinator received a project note stating that a draft is due next week, but the note does not specify the day.",
        "The coordinator asks the manager to clarify which day next week the draft is due.",
        "Specify the exact day next week when the draft is due.","Next week",
        "The coordinator needs the exact date to schedule the remaining work.",
        "The note says the draft is due next week, but it does not give a day. Please tell me the exact day it is due so I can schedule the remaining work.",
        "The project note states that the draft is due next week but does not specify a date. Please confirm the exact due date so I can schedule the remaining work.",
        "The note says the draft is due next week, but it does not give a day. Could you please let me know the exact day it is due so I can schedule the remaining work?",
        "The project note states that the draft is due next week but does not specify a date. Could you please confirm the exact due date so I can schedule the remaining work?",
    ),
    make_family(
        "IWA_004","workload_concern","upward","analyst","manager",
        "An analyst is already assigned two deliverables due on Friday and is given a third assignment with the same deadline.",
        "The analyst tells the manager that completing all three assignments by Friday is not feasible and asks which task should be prioritized.",
        "Clarify which of the three Friday assignments should be prioritized.","Friday",
        "All three assignments currently have the same deadline, and the analyst cannot complete all three by that time.",
        "I already have two deliverables due Friday, and this adds a third. I cannot complete all three by Friday. Please tell me which task I should prioritize.",
        "I currently have two deliverables due Friday, and this assignment creates a third concurrent deadline. Completing all three by Friday is not feasible. Please confirm which assignment should receive priority.",
        "I wanted to flag that I already have two deliverables due Friday, and this adds a third. I cannot complete all three by Friday. Could you please let me know which task I should prioritize?",
        "I wanted to flag that I currently have two deliverables due Friday, and this assignment creates a third concurrent deadline. Completing all three by Friday is not feasible. Could you please confirm which assignment should receive priority?",
    ),
    make_family(
        "IWA_005","error_identification","peer","analyst","analyst",
        "Two analysts are preparing a shared budget table, and one formula currently counts the same expense category twice.",
        "One analyst points out the duplicate calculation and asks the colleague to correct the formula before the table is submitted.",
        "Correct the formula that counts the same expense category twice.","Before submission",
        "The shared budget table should not be submitted with a duplicated expense calculation.",
        "This formula counts the same expense category twice. Please correct it before we submit the budget table.",
        "This formula counts the same expense category twice. Please correct the formula before submission of the budget table.",
        "I wanted to flag that this formula counts the same expense category twice. Could you please correct it before we submit the budget table?",
        "I wanted to flag that this formula counts the same expense category twice. Could you please correct the formula before submission of the budget table?",
    ),
    make_family(
        "IWA_006","overdue_contribution","peer","project_coordinator","project_coordinator",
        "Two project coordinators agreed that one would send a risk summary by Tuesday for inclusion in a joint project update.",
        "It is Wednesday and the risk summary has not been sent, so the other coordinator asks for it today.",
        "Send the overdue risk summary today.","Today",
        "The risk summary is needed for the joint project update.",
        "You have not sent the risk summary that was due Tuesday. Please send it today so I can include it in our project update.",
        "You have not provided the risk summary that was due Tuesday. Please provide it today for inclusion in the joint project update.",
        "I wanted to flag that you have not sent the risk summary that was due Tuesday. Could you please send it today so I can include it in our project update?",
        "I wanted to note that you have not provided the risk summary that was due Tuesday. Could you please provide it today for inclusion in the joint project update?",
    ),
    make_family(
        "IWA_007","process_change","peer","team_member","team_member",
        "Two team members currently keep separate copies of a shared task tracker, which requires them to reconcile changes manually.",
        "One team member proposes using one shared tracker instead of maintaining two separate copies.",
        "Use one shared task tracker instead of two separate copies.",None,
        "The current process requires manual reconciliation of duplicate tracker copies.",
        "We are keeping two copies of the task tracker and then reconciling them manually. I think we should use one shared tracker instead.",
        "We currently maintain two versions of the task tracker and reconcile them manually. I recommend moving to a single shared tracker.",
        "We are keeping two copies of the task tracker and then reconciling them manually. Could we consider using one shared tracker instead?",
        "We currently maintain two versions of the task tracker and reconcile them manually. Could we consider moving to a single shared tracker?",
    ),
    make_family(
        "IWA_008","revision_request","downward","manager","analyst",
        "An analyst submitted a draft section that does not include the required comparison of the three vendors.",
        "The manager asks the analyst to add the missing three-vendor comparison before the draft is circulated tomorrow.",
        "Add the required comparison of all three vendors.","Before circulation tomorrow",
        "The draft is scheduled to be circulated tomorrow and currently lacks a required comparison.",
        "The draft is missing the required comparison of the three vendors. Please add it before we circulate the document tomorrow.",
        "The draft does not include the required comparison of the three vendors. Please add this section before circulation of the document tomorrow.",
        "I wanted to flag that the draft is missing the required comparison of the three vendors. Could you please add it before we circulate the document tomorrow?",
        "I wanted to flag that the draft does not include the required comparison of the three vendors. Could you please add this section before circulation of the document tomorrow?",
    ),
    make_family(
        "IWA_009","priority_clarification","downward","team_lead","team_member",
        "A team member is working on a client briefing and an internal data-cleaning task, and both are currently scheduled for Friday.",
        "The team lead tells the team member to prioritize the client briefing and complete the data-cleaning task afterward.",
        "Prioritize the client briefing before the internal data-cleaning task.","Friday",
        "Both tasks are currently scheduled for Friday, so their order of priority needs to be clear.",
        "Both tasks are due Friday. Please prioritize the client briefing and complete the data-cleaning task afterward.",
        "Both assignments are scheduled for Friday. Please give priority to the client briefing and complete the internal data-cleaning task afterward.",
        "Both tasks are due Friday. Could you please prioritize the client briefing and complete the data-cleaning task afterward?",
        "Both assignments are scheduled for Friday. Could you please give priority to the client briefing and complete the internal data-cleaning task afterward?",
    ),
    make_family(
        "IWA_010","evidence_request","downward","manager","analyst",
        "An analyst estimated that a proposed process change would reduce processing time by 20 percent, but the draft does not show the basis for that estimate.",
        "The manager asks the analyst to provide the evidence or calculation supporting the 20 percent estimate before the proposal is reviewed.",
        "Provide the evidence or calculation supporting the 20 percent estimate.","Before proposal review",
        "The estimate will be considered in the review of the proposed process change.",
        "The draft says the change will cut processing time by 20 percent, but it does not show how that figure was calculated. Please provide the evidence or calculation before we review the proposal.",
        "The draft states that the change will reduce processing time by 20 percent but does not document the basis for that estimate. Please provide the supporting evidence or calculation before review of the proposal.",
        "I wanted to flag that the draft says the change will cut processing time by 20 percent, but it does not show how that figure was calculated. Could you please provide the evidence or calculation before we review the proposal?",
        "I wanted to flag that the draft states that the change will reduce processing time by 20 percent, but it does not show the basis for that estimate. Could you please provide the supporting evidence or calculation before review of the proposal?",
    ),
]

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for family in families:
        path = OUT_DIR / f"{family['family_id']}.json"
        path.write_text(json.dumps(family, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated {len(families)} new Intercultural Workplace AI pilot families.")

if __name__ == "__main__":
    main()
