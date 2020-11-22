import React, { useState } from 'react';
import {
  Form,
  Container,
  Accordion,
  Card,
  Button,
  ListGroup,
  Badge,
  Alert,
  Table
} from 'react-bootstrap';
import Fuse from 'fuse.js';
import data from './nd_s21.json';
const newData = Object.keys(data).map(key => {
  return {id: key, ...data[key]}
});


const fuseOptions = {
  useExtendedSearch: true,
  keys: [
    'title',
    'longTitle',
    'instructors',
    'id',
    'attributes'
  ]
};

const App = () => {

  // hook into React state
  const [results, setResults] = useState([]);
  const [engine] = useState(new Fuse(newData, fuseOptions));
  const [error, setError] = useState(false);
  
  // only search on enter keypress
  const onSearchKeyPress = (event) => {
    if (event.key === 'Enter') {
      if (event.target.value.length < 3) {
        setError(true);
      } else {
        setError(false);
        setResults(engine.search(event.target.value));
      }
    }
  };


  // renders accordion section header and body
  const renderSection = (section) => {
    return (
      <tr>
        <td>{section.section}</td>
        <td>{section.crn}</td>
        <td>{section.instructor.split('\n').join('; ')}</td>
        <td>{section.when.join('; ')}</td>
        <td>{section.where.join('; ')}</td>
        <td>{section.openSeats} / {section.maxSeats}</td>
      </tr>
    );
  };

  const renderResultBody = (item) => {
    return (
      <React.Fragment>
        
        <Card.Header>Course Description</Card.Header>
        <Card.Body>{item.description}</Card.Body>
        <br />

        <Card.Header>Course Attributes</Card.Header>
        <ListGroup variant="flush">
          {item.attributes.map(attr => {
            return (
              <ListGroup.Item>{attr}</ListGroup.Item>
            );
          })}
        </ListGroup>
        <br />
        
        <Card.Header>Course Sections</Card.Header>
        <Table>
          <thead>
            <tr>
              <th>#</th>
              <th>CRN</th>
              <th>Instructor(s)</th>
              <th>Time(s)</th>
              <th>Place(s)</th>
              <th>Open Seat(s)</th>
            </tr>
          </thead>
          <tbody>
            {item.sections.map(renderSection)}
          </tbody>
        </Table>

      </React.Fragment>
    );
  };

  const renderResult = (searchResult) => {
    const { item } = searchResult;
    return (
      <Accordion key={item.id}>
        <Card>

          {/* Clickable always-visible part */}
          <Accordion.Toggle as={Button} variant="secondary" eventKey="0">
            {item.longTitle ? item.longTitle : item.title} ({item.department}{item.courseId}) <Badge variant="dark">{item.instructors.length} Instructors</Badge>
          </Accordion.Toggle>

          {/* Data, not-immediately-visible part */}
          <Accordion.Collapse eventKey="0">
            <Card.Body>
              {renderResultBody(item)}
            </Card.Body>
          </Accordion.Collapse>
          
        </Card>
      </Accordion>
    );
  }

  return (
    <Container className="App mt-3" fluid>
      
      <h6>ND Class Search for Spring Semester 2021</h6>
      {/* Search box */}
      <Form id="userSearchForm" onSubmit={e => e.preventDefault()}>
        <Form.Control type="text" onKeyPress={onSearchKeyPress} />
        <Form.Text className="text-muted">
          Enter some search term(s) and press <code>&lt;Enter&gt;</code>. Also, searches are limited to at most <code>600</code> results (laggy otherwise).
        </Form.Text>
      </Form>

      {/* Neat line */}
      <hr />

      {/* If we are erroring */}
      <Alert variant="danger" show={error}>
          Please enter more than 3 characters.
      </Alert>

      {/* Render entire list */}
      {results.slice(0, 600).map(renderResult)}

    </Container>
  );
};

export default App;