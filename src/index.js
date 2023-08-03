import React from "react";
import ReactDOM from "react-dom";
import { createRoot } from "react-dom/client";

import SkillCard from "./SkillCard";

const rootElement = document.getElementById("skill-card-root");
const root = createRoot(rootElement);

root.render(
  <React.StrictMode>
    <SkillCard />
  </React.StrictMode>
);
