import React, { useState, useEffect, CSSProperties } from "react";
import ReactDOM from "react-dom";

import { FaAngleLeft, FaAngleRight } from "react-icons/fa6";

import "./SkillCard.scss";

const CARDS: number = 10;
const MAX_VISIBILITY: number = 3;

interface CardProps {
  title: string;
  content: string;
}

const Card: React.FC<CardProps> = ({ title, content }) => (
  <div className="skill-card">
    <h2>{title}</h2>
    <p>{content}</p>
  </div>
);

interface CarouselProps {
  children: React.ReactNode;
}

const Carousel: React.FC<CarouselProps> = ({ children }) => {
  const [active, setActive] = useState<number>(2);
  const count: number = React.Children.count(children);

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
      {React.Children.map(children, (child: React.ReactElement, i: number) => (
        <div
          className="card-container"
          style={
            {
              "--active": i === active ? 1 : 0,
              "--offset": (active - i) / 3,
              "--direction": Math.sign(active - i),
              "--abs-offset": Math.abs(active - i) / 3,
              "--pointer-events": active === i ? "auto" : "none",
              opacity: Math.abs(active - i) >= MAX_VISIBILITY ? "0" : "1",
              display: Math.abs(active - i) > MAX_VISIBILITY ? "none" : "block",
            } as CSSProperties
          }
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

const SkillCard: React.FC = () => {
  const [cardsData, setCardsData] = useState<any>(); // Use a more specific type if possible

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
          cardsData.labels.map((label: string, i: number) => (
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
