import { useEffect, useState } from "react";
import { useAuth } from "./hooks/useAuth";
import { useSession } from "./hooks/useSession";
import { AccountView } from "./views/AccountView";
import { ActiveSessionView } from "./views/ActiveSessionView";
import { ProblemSelectionView } from "./views/ProblemSelectionView";
import { SessionCompleteView } from "./views/SessionCompleteView";

type HomeScreen = "calculator" | "account";

export default function App() {
  const auth = useAuth();
  const session = useSession();
  const [homeScreen, setHomeScreen] = useState<HomeScreen>("calculator");

  useEffect(() => {
    if (session.view !== "selection") {
      setHomeScreen("calculator");
    }
  }, [session.view]);

  return (
    <main className="app">
      {session.view === "selection" && homeScreen === "account" ? (
        <AccountView auth={auth} onBack={() => setHomeScreen("calculator")} />
      ) : null}

      {session.view === "selection" && homeScreen === "calculator" ? (
        <ProblemSelectionView
          problemInput={session.problemInput}
          onProblemInputChange={session.setProblemInput}
          onStartSession={session.handleStartSession}
          onTryExample={session.handleTryExample}
          onSelectStarter={session.handleSelectStarter}
          onUseExpression={session.applyExpression}
          loading={session.problemLoading}
          resuming={session.resuming}
          error={session.problemError}
          auth={auth}
          onOpenAccount={() => setHomeScreen("account")}
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
          submitting={session.submitting}
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