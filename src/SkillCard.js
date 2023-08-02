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
    <Card title={"Card " + 1} content="dddddddddddasdad" />
  </div>
);

export default SkillCard;
