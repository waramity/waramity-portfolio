import React, { useState } from "react";
import ReactDOM from "react-dom";

import "./SkillCard.scss";

const CARDS = 10;
const MAX_VISIBILITY = 3;

const Card = ({ title, content }) => (
  <div className="card">
    <h2>{title}</h2>
    <p>{content}</p>
  </div>
);

const SkillCard = () => (
  <div className="mt-5">
    <Card
      title={"Card " + 1}
      content="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    />
  </div>
);

export default SkillCard;
