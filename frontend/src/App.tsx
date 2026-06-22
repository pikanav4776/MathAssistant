import { useAuth } from "./hooks/useAuth";
import { useSession } from "./hooks/useSession";
import { ActiveSessionView } from "./views/ActiveSessionView";
import { ProblemSelectionView } from "./views/ProblemSelectionView";
import { SessionCompleteView } from "./views/SessionCompleteView";

export default function App() {
  const auth = useAuth();
  const session = useSession();

  return (
    <main className="app">
      {session.view === "selection" ? (
        <ProblemSelectionView
          problemInput={session.problemInput}
          onProblemInputChange={session.setProblemInput}
          onStartSession={session.handleStartSession}
          onTryExample={session.handleTryExample}
          onUseExpression={session.applyExpression}
          loading={session.problemLoading}
          error={session.problemError}
          auth={auth}
        />
      ) : null}

      {session.view === "session" ? (
        <ActiveSessionView
          state={session.state}
          stepInput={session.stepInput}
          onStepInputChange={session.setStepInput}
          onSubmitStep={session.handleSubmitStep}
          onGiveUp={session.handleGiveUp}
          onUseExpression={session.applyExpression}
          feedback={session.feedback}
          showFeedback={session.showFeedback}
          inputError={session.inputError}
          submitDisabled={session.submitDisabled}
          giveUpDisabled={session.giveUpDisabled}
          attemptHistoryOpen={session.attemptHistoryOpen}
          onAttemptHistoryToggle={session.setAttemptHistoryOpen}
          allGreenDots={session.allGreenDots}
        />
      ) : null}

      {session.view === "complete" ? (
        <SessionCompleteView
          mode={session.completeMode}
          state={session.state}
          onTryAnother={session.handleTryAnother}
        />
      ) : null}
    </main>
  );
}