import React, { useState, useEffect, CSSProperties } from "react";
import ReactDOM from "react-dom";

import { FaAngleLeft, FaAngleRight } from "react-icons/fa6";

import "./SkillCard.scss";

const CARDS: number = 10;
const MAX_VISIBILITY: number = 3;

interface CardProps {
  title: string;
  image: string;
}

const Card: React.FC<CardProps> = ({ title, image }) => (
  <div className="skill-card row p-5">
    <div className="col-12 text-center pt-3 mt-2">
      <img src={image} alt={title} className="w-50" />
    </div>
    <div className="col-12">
      <h2 className="text-white">{title}</h2>
    </div>
  </div>
);

interface CarouselProps {
  children: React.ReactNode;
  active: number; // Add the active prop
  setActive: React.Dispatch<React.SetStateAction<number>>; // Add the setActive prop
}

const Carousel: React.FC<CarouselProps> = ({ children, active, setActive }) => {
  // const [active, setActive] = useState<number>(0);
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

interface CardData {
  images: string[];
  labels: string[];
  title: string;
}

interface CurrentCard {
  images: string[];
  labels: string[];
}

const SkillCard: React.FC = () => {
  const [cardsData, setCardsData] = useState<CardData[]>(); // Use a more specific type if possible
  const [currentCard, setCurrentCard] = useState<CurrentCard>(); // Use the initial image source here

  const [active, setActive] = useState<number>(0); // Move active state here

  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    fetch("/en/get_skill_nav")
      .then((response) => response.json())
      .then((data) => {
        setCardsData(data);
        setCurrentCard({ labels: data[0].labels, images: data[0].images });
      })
      .catch((error) => console.error("Error fetching data:", error));
  }, []);

  const handleCardChange = (card: CurrentCard, index: number) => {
    setCurrentCard(card);
    setActive(0);

    setActiveIndex(index);
  };

  return (
    <div className="row">
      <div className="col-6">
        <ul className="nav nav-underline mb-3 flex-column">
          {cardsData ? (
            cardsData.map((item: CardData, i: number) => (
              <li className="nav-item" role="presentation">
                <button
                  onClick={() =>
                    handleCardChange(
                      {
                        labels: item.labels,
                        images: item.images,
                      },
                      i // Pass the current index here
                    )
                  }
                  className={`nav-link text-secondary ${
                    i === activeIndex ? "active" : ""
                  }`}
                  style={
                    {
                      fontSize: "1.33rem",
                    } as CSSProperties
                  }
                >
                  {item.title}
                </button>
              </li>
            ))
          ) : (
            <p>Loading data...</p>
          )}
        </ul>
      </div>
      <div className="col-6">
        <div className="mt-5">
          <Carousel active={active} setActive={setActive}>
            {currentCard ? (
              currentCard.labels.map((label: string, i: number) => (
                <Card
                  key={i}
                  title={label}
                  image={"/static/data/skill/" + currentCard.images[i]}
                />
              ))
            ) : (
              <p>Loading data...</p>
            )}
          </Carousel>
        </div>
      </div>
    </div>
  );
};

export default SkillCard;
