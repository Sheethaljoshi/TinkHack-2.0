"use client"
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Card from '../components/card';
import { MdEmojiPeople } from "react-icons/md";
import SubNav from '../components/subnav';



const CardPage: React.FC = () => {
    const [relatedPeople, setRelatedPeople] = useState([{name:"",relation:"",occupation:"",description:""}]);
    const [originalPeople, setOriginalPeople] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const url = `http://127.0.0.1:8000/get/person?email=sh33thal24@gmail.com&first_name=Sheethal&last_name=Joshi%20Thomas`;
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                console.log(data);
                setRelatedPeople(data);
                setOriginalPeople(data);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };
    
        fetchData();
    }, []);


    // Function to sort people based on alphabetical order of name
    const sortPeopleAlphabetically = () => {
        const sortedPeople = [...relatedPeople].sort((a, b) => a.name.localeCompare(b.name));
        setRelatedPeople(sortedPeople);
    };

    const sortPeopleRecentlyAdded = () => {
        const reversedPeople = [...originalPeople].reverse(); // Reverse the current array
        setRelatedPeople(reversedPeople);
    };

    return (
        <div className="flex-grow">
            <div className='text-3xl font-extrabold pl-10 pt-3 pb-8 z-[1]'>
                <SubNav
                    mainButtonText="History"
                    parentText="Filter"
                    submenu1Text="Recently Added"
                    submenu2Text="Alphabetical Order"
                    item1Text="Add new"
                    item3Text="Add new"
                    onSubmenu2Click={sortPeopleAlphabetically}
                    onSubmenu1Click={sortPeopleRecentlyAdded}
                />
            </div>
            <div className="flex justify-center items-center">
                <div className="grid  grid-cols-1 lg:grid-cols-2 gap-9 w-full max-w-screen-lg lg:mx-auto ml-11">
                    {relatedPeople.map((person, person_index) => (
                        <Card person_index={person_index} key={person_index} {...person} />
                    ))}
                </div>
            </div>
        </div>
    );
};

export default CardPage;
