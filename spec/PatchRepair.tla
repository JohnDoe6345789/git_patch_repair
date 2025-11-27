----------------------------- MODULE PatchRepair -----------------------------
EXTENDS Naturals

(*
  High-level TLA+ spec of the iterative patch repair loop.

  Intuition
  =========
  - State variables:
      patch   : current patch text (abstract element of Patch)
      iter    : current iteration index
      gitOK   : TRUE iff `git apply --check` would succeed on `patch`
  - Constants:
      Patch   : abstract set of all syntactically possible patches
      MaxIter : maximum number of iterations (Nat > 0)
      GitOk   : abstract predicate giving git validation result
      Repair  : abstract relation that gives “repaired” patches

  The algorithm:
  --------------
  1. Start from some initial patch (e.g. input diff file), iter = 0.
  2. Repeatedly:
       - Clean + analyse + repair patch structurally (abstracted as Repair).
       - Optionally call GitOk(patch) to see if git accepts it.
       - Stop when:
           * GitOk(patch) = TRUE (success), or
           * iter reaches MaxIter, or
           * further repair steps make no textual progress.
*)

(***************************************************************************)
(* CONSTANTS                                                               *)
(***************************************************************************)

CONSTANTS
    Patch,      \* Set of all possible patches (abstract values)
    MaxIter,    \* Maximum number of iterations (Nat, > 0)
    GitOk,      \* Constant operator: GitOk(p) \in BOOLEAN for p \in Patch
    Repair      \* Constant operator: Repair(p) ⊆ Patch for p \in Patch

(*
  Sanity assumptions on the abstract operators.
*)
ASSUME /\ MaxIter \in Nat \ {0}
       /\ \A p \in Patch : GitOk(p) \in BOOLEAN
       /\ \A p \in Patch : Repair(p) \subseteq Patch

(***************************************************************************)
(* STATE VARIABLES                                                         *)
(***************************************************************************)

VARIABLES
    patch,      \* current patch state
    iter,       \* iteration counter
    gitOK       \* cached result of GitOk(patch)

vars == << patch, iter, gitOK >>

(***************************************************************************)
(* INITIALISATION                                                          *)
(***************************************************************************)

Init ==
    /\ patch \in Patch
    /\ iter = 0
    /\ gitOK = GitOk(patch)

(***************************************************************************)
(* TRANSITION RELATION                                                     *)
(***************************************************************************)

(*
  Once gitOK is TRUE we conceptually “stop changing” the patch and iteration.
  This is the quiescent / terminal behaviour.
*)
StayDone ==
    /\ gitOK
    /\ patch' = patch
    /\ iter'  = iter
    /\ gitOK' = gitOK

(*
  A repair step that actually changes the patch. This abstracts:
    - basic_clean
    - parse_diff
    - filter_or_repair_files(allow_repairs = TRUE)
    - render_patch
  into a single Repair operator.
*)
RepairStep ==
    /\ ~gitOK
    /\ iter < MaxIter
    /\ \E pNew \in Repair(patch) :
          /\ pNew # patch
          /\ patch' = pNew
          /\ iter'  = iter + 1
          /\ gitOK' = GitOk(pNew)

(*
  A “no-progress” step: we advance iter but keep the patch unchanged.
  This corresponds to a situation where the repair logic cannot improve
  the patch (e.g. Repair(patch) = {patch} or is empty in the model).
*)
NoProgressStep ==
    /\ ~gitOK
    /\ iter < MaxIter
    /\ patch' = patch
    /\ iter'  = iter + 1
    /\ gitOK' = gitOK

(*
  In practice you might choose not to allow NoProgressStep and instead
  stop immediately once a repair pass makes no changes. Here we model it
  explicitly and rely on the termination condition below.
*)

Next ==
    StayDone
    \/ RepairStep
    \/ NoProgressStep

(***************************************************************************)
(* SPECIFICATION AND PROPERTIES                                            *)
(***************************************************************************)

(*
  Standard TLA+ “always Next or stutter” spec.
*)
Spec ==
    Init /\ [][Next]_vars

(*
  Type / range invariant for sanity checking.
*)
TypeInv ==
    /\ patch \in Patch
    /\ iter  \in Nat
    /\ iter  <= MaxIter
    /\ gitOK \in BOOLEAN

(*
  Termination condition of the algorithm:
  Either gitOK is TRUE or we have reached the iteration budget.
*)
Terminated ==
    gitOK \/ iter = MaxIter

(*
  Safety: types are preserved in all reachable states.
*)
THEOREM Spec => []TypeInv

(*
  Optional: a simple liveness obligation you might want to check or
  refine with fairness:

    Eventually either we succeed (gitOK) or we consider ourselves done
    because we exhausted iterations.

  In general you may need fairness assumptions on RepairStep to prove
  stronger properties.
*)
TerminationProperty ==
    Spec => <>Terminated

=============================================================================
