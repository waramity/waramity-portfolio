import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";

import { FaAngleLeft, FaAngleRight } from "react-icons/fa6";

import "./SkillCard.scss";

const CARDS = 10;
const MAX_VISIBILITY = 3;

const Card = ({ title, content }) => (
  <div className="skill-card">
    <h2>{title}</h2>
    <p>{content}</p>
  </div>
);

const Carousel = ({ children }) => {
  const [active, setActive] = useState(2);
  const count = React.Children.count(children);

  return (
    <div className="carousel">
      {active > 0 && (
        <button
          className="skill-card-nav left"
          onClick={() => setActive((i) => i - 1)}
        >
          <FaAngleLeft />
        </button>
      )}
      {React.Children.map(children, (child, i) => (
        <div
          className="card-container"
          style={{
            "--active": i === active ? 1 : 0,
            "--offset": (active - i) / 3,
            "--direction": Math.sign(active - i),
            "--abs-offset": Math.abs(active - i) / 3,
            "pointer-events": active === i ? "auto" : "none",
            opacity: Math.abs(active - i) >= MAX_VISIBILITY ? "0" : "1",
            display: Math.abs(active - i) > MAX_VISIBILITY ? "none" : "block",
          }}
        >
          {child}
        </div>
      ))}
      {active < count - 1 && (
        <button
          className="skill-card-nav right"
          onClick={() => setActive((i) => i + 1)}
        >
          <FaAngleRight />
        </button>
      )}
    </div>
  );
};

const SkillCard = () => {
  const [cardsData, setCardsData] = useState();

  useEffect(() => {
    fetch("/en/get_skill_data/2")
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        setCardsData(data);
      })
      .catch((error) => console.error("Error fetching data:", error));
  }, []);

  console.log(cardsData);
  console.log(typeof cardsData);

  return (
    <div className="mt-5">
      <Carousel>
        {cardsData ? (
          cardsData.labels.map((label, i) => (
            <Card key={i} title={label} content="" />
          ))
        ) : (
          <p>Loading data...</p>
        )}
      </Carousel>
    </div>
  );
};

export default SkillCard;
