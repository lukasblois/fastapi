from sqlalchemy.orm import Session
from fastapi import status, HTTPException, Depends, APIRouter, Request
from ..database import get_db
from .. import models, schemas, utils, oauth2
from ..limiter import limiter
from ..config import settings

router = APIRouter(
    prefix='/users',
    tags=['Users']
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
@limiter.limit(settings.limit_users_create)
def create_user(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    user_dict = user.model_dump()
    user_dict['password'] = utils.hash(user_dict['password'])

    new_user = models.User(**user_dict)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{id}", response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return user


@router.post("/check-password-strength", response_model=schemas.PasswordStrengthResponse)
def check_password_strength(email: str = "", password: str = ""):
    result = utils.validate_password_strength(password, email)

    return {
        "is_strong": result[0],
        "score": result[2],
        "max_score": 4,
        "crack_time": result[3],
        "message": result[1]
    }


@router.put("/password-reset", status_code=status.HTTP_200_OK)
@limiter.limit(settings.limit_password_reset)
def reset_password(request: Request,
                   password_data: schemas.PasswordResetInApp,
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(oauth2.get_current_user)
                   ):
    if not utils.verify(password_data.old_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current password incorrect"
        )

    if password_data.old_password.strip() == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password"
        )

    hashed_password = utils.hash(password_data.new_password)

    user_query = db.query(models.User).filter(
        models.User.id == current_user.id)
    user_query.update({"password": hashed_password}, synchronize_session=False)

    db.commit()

    return {"detail": "Password updated successfully"}
