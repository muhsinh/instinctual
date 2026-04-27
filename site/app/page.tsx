import { Hero } from "./components/Hero";
import { InteractiveDemo } from "./components/InteractiveDemo";
import { HowItWorks } from "./components/HowItWorks";
import { DemoSection } from "./components/DemoSection";
import { UseCases } from "./components/UseCases";
import { Comparison } from "./components/Comparison";
import { Pricing } from "./components/Pricing";
import { Security } from "./components/Security";
import { Team } from "./components/Team";
import { EarlyAccess } from "./components/EarlyAccess";
import { Footer } from "./components/Footer";

export default function Home() {
  return (
    <main>
      <Hero />
      <InteractiveDemo />
      <HowItWorks />
      <DemoSection />
      <UseCases />
      <Comparison />
      <Pricing />
      <Security />
      <Team />
      <EarlyAccess />
      <Footer />
    </main>
  );
}
