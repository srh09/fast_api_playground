from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from db import session
from models.character import Character
from models.comic import Comic
from api.services import marvel

router = APIRouter()


@router.get('/api/v1/comics/character/{marvel_id}')
async def get_comics_by_character(marvel_id: int, db: Session = Depends(session.get_db)):
    main: Character = db.query(Character).filter(Character.marvel_id == marvel_id).first()
    if not main.comics_updated:
        # Get the Character's Comics from Marvel
        comics_relationships, ucis = await marvel.get_comics_by_character_id(main.marvel_id)

        # Get all of the Characters related to the Comics
        character_id2character = {}
        for uci in ucis:
            character: Character = db.query(Character).filter(Character.marvel_id == uci).first()
            if not character:
                character = await marvel.get_character_by_id(uci)
                print(f'getting {character.name} from marvel-----------------')
                db.add(character)
            character_id2character[character.marvel_id] = character

        for comics_relationship in comics_relationships:
            comic: Comic = comics_relationship['comic']

            db_comic: Comic = db.query(Comic).filter(Comic.marvel_id == comic.marvel_id).first()
            if not db_comic:
                # This Comic does not yet exist add the Character relationships then store
                for character_id in comics_relationship['character_ids']:
                    comic.characters.append(character_id2character[character_id])
                print(f'storing comic {comic.title}---------------')
                db.add(comic)

        main.comics_updated = datetime.now(timezone.utc)
        db.add(main)
        db.commit()

    comics: List[Comic] = main.comics
    id2comic = {}
    for comic in comics:
        id2comic[comic.marvel_id] = comic.to_dict()

    id2affiliated_character = {}
    characters = set()
    for comic in comics:
        characters.update(comic.characters)
    for character in characters:
        id2affiliated_character[character.marvel_id] = character.to_dict()

    return {
        'comic_id2comic': id2comic,
        'affiliated_characters': id2affiliated_character,
        'discovered_characters': [character.name for character in db.query(desc(Character.created)).limit(50).all()],
    }