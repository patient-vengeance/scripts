import csv

from bs4 import BeautifulSoup
from pydantic import BaseModel

TAIPEI = "臺北市"
NEW_TAIPEI = "新北市"


class Lecturer(BaseModel):
    name: str
    major: set[str]
    city: set[str]


def main():
    with open("index.html", "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "html.parser")

    # Select the div with id "tableData"
    table_data_div = soup.select_one("div#tableData")

    if table_data_div:
        lecturers: list[Lecturer] = list()
        cols = table_data_div.select("ul")

        for col in cols:
            col_name = col.select_one("li.colname")
            name = col_name.select("span")[-1].text

            col_course_bound = col.select_one("li.colcourseBound")
            major = set(
                map(lambda x: x.text, col_course_bound.select("span.colParentClass"))
            )

            col_expect_city_bound = col.select_one("li.colexpectCityBound")
            city = set(
                filter(
                    lambda x: x != "無",
                    map(
                        lambda x: x.text.strip(","),
                        col_expect_city_bound.select("span")[1:],
                    ),
                )
            )

            lecturers.append(
                Lecturer(
                    name=name,
                    major=major,
                    city=city,
                )
            )

        csv_rows: list[list] = list()
        for lecturer in filter(
            lambda x: TAIPEI in x.city or NEW_TAIPEI in x.city,
            lecturers,
        ):
            for major in lecturer.major:
                csv_rows.append(
                    [
                        lecturer.name,
                        major,
                        int(TAIPEI in lecturer.city),
                        int(NEW_TAIPEI in lecturer.city),
                    ]
                )
        with open("lecturers.csv", "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["name", "major", "is_in_taipei", "is_in_new_taipei"])
            writer.writerows(csv_rows)

    else:
        print("No div with id 'tableData' found in the HTML.")


if __name__ == "__main__":
    main()
